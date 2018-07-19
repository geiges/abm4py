#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (c) 2017
Global Climate Forum e.V.
http://www.globalclimateforum.org

This file is part of GCFABM.

GCFABM is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

GCFABM is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with GCFABM.  If not, see <http://www.gnu.org/licenses/>.

"""


#%% load modules

import sys 
import os
import numpy as np

import time
import random


import matplotlib.pyplot as plt
home = os.path.expanduser("~")
sys.path.append('../')


from lib import World, Agent, Location #, GhostAgent, World,  h5py, MPI
from lib.traits import  Mobile
from lib.future_traits import Collective
from lib import core

import tools_for_06 as tools

#%% SETUP
EXTEND = 20
N_PEOPLE = 150
INFECTIOUSNESS = 0.65
CHANCE_RECOVER = 0.75
DURATION = 20
LIFESPAN = 2600             # Lifespan of an agent, 2600 weeks = 50 years
CARRYING_CAPACITY = 300
CHANCE_REPRODUCE = 1
IMMUNITY_DURATION = 52
# MAX_AGENTS = max(CARRYING_CAPACITY, EXTEND**2)
MAX_AGENTS = 10000

#%% People class
class People(Agent, Mobile):


    def __init__(self, world, **kwAttr):
        #print(kwAttr['coord'])
        Agent.__init__(self, world, **kwAttr)
        Mobile.__init__(self, world, **kwAttr)
        
        self.getAgent = world.getAgent

    def __descriptor__():
        """
        This desriptor defines the agent attributes that are saved in the 
        agent graph an can be shared/viewed by other agents and acessed via 
        the global scope of the world class.
        All static and dynamic attributes can be accessed by the agent by:
            1) agent.get('attrLabel') / agent.set('attrLabel', value)
            2) agent.attr['attrLabel']
            3) agent.attr['attrLabel']
        """
        classDesc = dict()
        classDesc['nameStr'] = 'Location'
        # Static properites can be re-assigned during runtime, but the automatic
        # IO is only logging the initial state
        classDesc['staticProperties'] =  []          
        # Dynamic properites can be re-assigned during runtime and are logged 
        # per defined time step intervall (see core.IO)
        classDesc['dynamicProperties'] =   [('coord', np.int16, 2),
                                            ('sick', np.bool,1),
                                            ('remainingImmunity', np.int16),
                                            ('sickTime', np.int16),
                                            ('age', np.int16)]    
        return classDesc
    
    def register(self,world):

        Agent.register(self, world)
        self.loc = locDict[(x,y)]
        world.addLink(LINK_PEOPLE, self.loc.nID, self.nID)
        
    def getSick(self):
        """
        This function makes the person infectious.
        """
        self['sick'] = True
        self['remainingImmunity'] = 0
        
    def getHealthy(self):
        """
        This function makes the person healthy.
        """
        self['sick'] = False
        self['remainingImmunity'] = 0
        self['sickTime'] = 0
    
    def becomeImmune(self):
        """
        This function makes the person immune.
        """
        self['sick'] = False
        self['remainingImmunity'] = IMMUNITY_DURATION
        self['sickTime'] = 0
        
    def getOlder(self):
        """ 
        With every step the people become one week older. They die of old 
        age once they exceed the lifespan.
        
        """
        self['age'] += 1
        if self['age'] > LIFESPAN:
            self.delete(world)
        if self['remainingImmunity'] > 0:
            self['remainingImmunity'] -= 1
        if self['sick']:
            self['sickTime'] += 1
            
        
    def move(self):
        """ 
        This function lets the people move to a new position randomly 
        drawn around its current position. It is made sure, that they do 
        not leave the premises. Also links to old neighbours are deleted 
        and new links established.
        
        """
        (dx,dy) = np.random.randint(-1,2,2)
        newX, newY = (self.attr['coord'] + [ dx, dy])
        #warum oben runde und hier eckige Klammern um dx, dy
        
        newX = min(max(0,newX), EXTEND-1)
        newY = min(max(0,newY), EXTEND-1)
        #print(self.nID)
        Mobile.move(self, newX, newY, LINK_PEOPLE)
        
    def infect(self):
        if random.random() < INFECTIOUSNESS:
            for peopleID in self.loc.getPeerIDs(LINK_PEOPLE):
                people = self.getAgent(peopleID)   
                if people['remainingImmunity']==0 and not people.attr['sick']:
                    people.getSick()
                
    def recoverOrDie(self):
        if self['sickTime'] > DURATION:
            if np.random.random(1) < CHANCE_RECOVER:
                self.becomeImmune()
            else:
                #print('Person died')
                self.delete(world)
                
    def reproduce(self):
        if world.nAgents(PEOPLE) < CARRYING_CAPACITY and np.random.random(1) < CHANCE_REPRODUCE:

            newPerson = People(world, 
                               coord=self['coord'], 
                               age=1)
            newPerson.getHealthy()
            newPerson.register(world)
                
#%%
world = World(agentOutput=False,
                  maxNodes=MAX_AGENTS,
                  maxLinks=200000)

world.setParameter('extend', EXTEND)
#%% register a new agent type with four attributes

PATCH = world.registerAgentType(Location,
                               staticProperties  = [('coord', np.int16, 2)],
                               dynamicProperties = [])

PEOPLE = world.registerAgentType(People)
                    



#%% register a link type to connect agents
PATCHWORK = world.registerLinkType('patchwork', PATCH, PATCH, staticProperties=[('weig',np.float32,1)])

LINK_PEOPLE = world.registerLinkType('patchLink', PEOPLE, PATCH)

world.registerGrid(PATCH, PATCHWORK)

IDArray = np.zeros([EXTEND, EXTEND])

tt = time.time()
for x in range(EXTEND):
    for y in range(EXTEND):
        
        patch = Location(world, 
                      coord=(x,y))
        patch.register(world)
        IDArray[x,y] = patch.nID
        

connBluePrint = world.grid.computeConnectionList(radius=2.5)
world.grid.connectNodes(IDArray, connBluePrint, PATCHWORK, Location)


# Sheep and wolves are assigned locations and registered to the world.

locDict = world.getLocationDict()
for iPeople in range(N_PEOPLE):
    (x,y) = np.random.randint(0,EXTEND,2)
    
    people = People(world,
                  coord=(x,y),
                  age=np.random.randint(0, LIFESPAN, 1),
                  sickTime=0,
                  remainingImmunity=0,
                  sick=False)   
    people.register(world)
    
    
del people

for people in world.random.nChoiceOfType(10, PEOPLE):
    people.getSick()



plott = tools.PlotClass(world)
    
#%%
iStep = 0
while True:
    iStep +=1
    tt = time.time()
    for people in world.getAgents.byType(PEOPLE):
        people.move()
        people.getOlder()
        
        
        if people['sick']:
            people.recoverOrDie()
        if people['sick']:
            people.infect()
        else:
            people.reproduce()
              
     
    # This updates the plot.        
    coord = world.getAttrOfAgentType('coord', agTypeID=PEOPLE)
    if coord is not None:
        np.clip(coord, 0, EXTEND, out=coord)
        world.setAttrOfAgentType('coord', coord, agTypeID=PEOPLE)
        plott.update(world)
    
    # This gives the number of sheep, the number of wolves and of these
    # the number of hunting wolves as strings in the console.
    # nHunting = np.sum(world.getAttrOfAgentType('weight', agTypeID=WOLF) <1.0)        
    #print(str(time.time() - tt) + ' s')
    #print(str(world.nAgents(SHEEP)) + ' - ' + str(world.nAgents(WOLF)) + '(' + str(nHunting) + ')')
    iStep +=1
