import copy
import heapq
import metrics
import multiprocessing.pool as mpool
import os
import random
import shutil
import time
import math
from random import randint

width = 200
height = 16

options = [
    "-",  # an empty space
    "X",  # a solid wall
    "?",  # a question mark block with a coin
    "M",  # a question mark block with a mushroom
    "B",  # a breakable block
    "o",  # a coin
    "E",  # an enemy
    "|",  # a pipe segment
    "T",  # a pipe top
    
    #"f",  # a flag, do not generate
    #"v",  # a flagpole, do not generate
    #"m"  # mario's start position, do not generate
]

# The level as a grid of tiles


class Individual_Grid(object):
    __slots__ = ["genome", "_fitness"]

    def __init__(self, genome):
        self.genome = copy.deepcopy(genome)
        self._fitness = None

    # Update this individual's estimate of its fitness.
    # This can be expensive so we do it once and then cache the result.
    def calculate_fitness(self):
        measurements = metrics.metrics(self.to_level())
        # Print out the possible measurements or look at the implementation of metrics.py for other keys:
        # print(measurements.keys())
        # Default fitness function: Just some arbitrary combination of a few criteria.  Is it good?  Who knows?
        # STUDENT Modify this, and possibly add more metrics.  You can replace this with whatever code you like.
        coefficients = dict(
            meaningfulJumpVariance=0.5,
            negativeSpace=3.0,
            pathPercentage=0.7,
            emptyPercentage=0.3,
            linearity=-0.9,
            solvability=2.0
        )
        self._fitness = sum(map(lambda m: coefficients[m] * measurements[m],
                                coefficients))
        return self

    # Return the cached fitness value or calculate it as needed.
    def fitness(self):
        if self._fitness is None:
            self.calculate_fitness()
        return self._fitness

    # Mutate a genome into a new genome.  Note that this is a _genome_, not an individual!
    def mutate(self, genome):
        # STUDENT implement a mutation operator, also consider not mutating this individual
        # STUDENT also consider weighting the different tile types so it's not uniformly random
        # STUDENT consider putting more constraints on this to prevent pipes in the air, etc
        new_genome=copy.deepcopy(genome)
        # consider not mutating this individual
        if random.random() < .00001:
            return new_genome
        left = 1
        right = width - 1
        for y in range(height):
            for x in range(left, right):
                #print('Y: ',y,'X: ',x,'genome: ',genome)
                #if genome[y][x] == "|":
                    #genome[y-1][x] = "T"
                
                # small chance to mutate something from nothing "-"
                if genome[y][x] == "-":
                    if random.random() < .006:
                        #genome[y][x] = random.choices(options[0:6], k=width)
                        printOption = options[randint(2, 6)]
                        genome[y][x] = printOption #options[randint(0, 6)]
                        #print('Mutated genome[',y,'][',x,'] with ',printOption)
                        
                # small chance to remove something, not a pipe or ground tho
                #if genome[y][x] != "|" and genome[y][x] != "T" and genome[y][x] != "X":
                if genome[y][x] == "B": 
                    if random.random() <.17:
                        genome[y][x] = "-"
                elif genome[y][x] == "M":
                     if random.random() <.25:
                        genome[y][x] = "-"
                elif genome[y][x] == "o":
                    if random.random() <.001:
                        genome[y][x] = "-"
                elif genome[y][x] == "E":
                    if random.random() < .09: #.005
                        genome[y][x] = "-"
                elif genome[y][x] == "?": 
                    if random.random() < .15:
                        genome[y][x] = "-"
                
                if(x+4 < right):
                    # chance that a block will extend to the right, creating a platform
                    rando = random.random()
                    if (genome[y][x] == "B" or genome[y][x] == "?" or genome[y][x] == "M")and genome[y][x+1] == "-":
                        if random.random() < .01:
                            genome[y][x+1] = "M"
                            
                        elif random.random() < .1:
                            #print("?")
                            genome[y][x+1] = "?"     
                            
                        elif random.random() < .35:
                            genome[y][x+1] = "B" #??? was B
                            
                        elif random.random() < .40:
                            genome[y][x+1] = "X"
                    
                    if(y+1 < height):
                        # small chance to extend floating solid blocks
                        if genome[y][x] == "X" and genome[y+1][x] == "-":
                            if rando < .02:
                                genome[y][x+1] = "B" #??????????? was B
                            elif rando < .03:
                                genome[y][x+1] = "?"
                            elif rando < .2:
                                genome[y][x+1] = "X"
                                
                        
                        # chance to remove isolated solid blocks
                        if genome[y][x] == "X":
                            if genome[y+1][x-1] == "-" and genome[y+1][x] == "-" and genome[y+1][x+1] == "-" and genome[y][x-1] == "-" and genome[y][x+1] == "-":
                                if random.random() < .6:
                                    genome[y][x] = "-"
                            elif genome[y+1][x-1] == "-" and genome[y+1][x] == "-" and genome[y+1][x+1] == "-":
                                if random.random() < .4:
                                    genome[y][x] = "-"
                                    
                        # chance to remove enemies spawned too close to each other
                        if genome[y][x] == "E":
                            if genome[y+1][x-1] == "E" or genome[y+1][x] == "E" or genome[y+1][x+1] == "E" or genome[y][x-1] == "E" or genome[y][x+1] == "E" or genome[y-1][x-1] == "E" or genome[y-1][x] == "E" or genome[y-1][x+1] == "E":
                                if random.random() < .9:
                                    genome[y][x] = "-"
                            #elif genome[y+1][x-1] == "E" and genome[y+1][x] == "E" and genome[y+1][x+1] == "E":
                            #    if random.random() < .4:
                            #        genome[y][x] = "-"
                                    
                    # chance to generate "stairs"
                    if genome[y][x] == "X" and genome[y][x+1] == "X":
                        # to get more verticality to stairs, chance to extend plateus       ---- => --X-
                        #                                                                   -XX- => -XX-
                        if genome[y][x+2] == "-" and genome[y][x-1] == "X":                     
                            if random.random() < .4:
                                genome[y-1][x+1] = "X"
                        # to get more verticality to stairs and not a 'second ground level' X- => XX
                        # it will more often build near other, higher ground                XX => XX
                        elif genome[y-1][x] == "X" and genome[y-1][x+1] == "-":
                            if random.random() < .3:
                                #if random.random() < .6:
                                genome[y-1][x+1] = "X"
                                #else:
                                 #   genome[y-1][x] = "X"
                        # chance to start stairs
                        elif random.random() < .02:
                            if random.random() <.7:
                                genome[y-1][x+1] = "X"
                            else:
                                genome[y-1][x] = "X"
                
                    # start a gap in the ground
                    if genome[y][x] == "X" and genome[y][x+1] == "X" and genome[y][x+2] == "X":
                        if genome[y-1][x] != "|" and genome[y-1][x+1] != "|" and genome[y-1][x+2] != "|":
                            if random.random() < .02:
                                genome[y][x+1] = "-"
                                if random.random() < .3:
                                    genome[y][x+2] = "-"
                                    if random.random() < .3:
                                        genome[y][x+3] = "-"
                                        if random.random() < .3:
                                            genome[y][x+4] = "-"
                                            
                    # get rid of things clipping into pipes, on the right of the pipes
                    if (genome[y][x] == "|" or genome[y][x] == "T"): # and (genome[y][x+1] == "|" or genome[y][x+1] == "T"):
                        genome[y][x+1] == "-"
                    # get rid of anything clipping into pipes, above the pipes
                    if genome[y][x] == "T":
                        genome[y-1][x] = "-"
                        genome[y-1][x+1] = "-"
                    
                    if(y-3 > 0):
                        # start a pipe above solid ground "X"
                        if genome[y][x] == "X" and genome[y][x+1] == "X" and genome[y][x+2] == "X" and genome[y-1][x+1] != "|":
                            if genome[y-1][x] != "|" and genome[y-1][x] != "T" and genome[y-1][x+2] != "|" and genome[y-1][x+2] != "T":
                                if random.random() < .02:
                                    genome[y-1][x+1] = "|"
                                    if random.random() < 0.5:
                                        # continue building a pipe  
                                        genome[y-2][x+1] = "|"
                                        if random.random() < 0.7:
                                            genome[y-3][x+1] = "|"
                                            genome[y-4][x+1] = "T"
                                        else:
                                            genome[y-3][x+1] = "T"
                                    else:
                                        genome[y-2][x+1] = "T"
                        
                # remove any rogue, floating pipes here
                randoo = random.random()
                if(y+1 < height):
                    if genome[y][x] == "|": 
                        if (genome[y+1][x] != "|" and genome[y+1][x] != "X"): # or genome[y+1][x+1] != "X"):
                                genome[y][x] = "-"
                        if ((genome[y-1][x] != "|" and genome[y-1][x] != "T")):
                                genome[y][x] = "-"
                                
                    if genome[y][x] == "T":
                        if genome[y+1][x] == "-":
                            genome[y][x] = "-"
                        if (genome[y+1][x] == "X" and genome[y+1][x+1] == "-"):
                            genome[y][x] = "-"
                        if (genome[y+1][x] != "|" and genome[y+1][x] != "X"): # or genome[y+1][x+1] != "X"):
                            genome[y][x] = "-"
                    '''
                    # chance to remove "?" and "M" blocks if they cant even be reached by mario        
                    if (genome[y][x] == "?" or genome[y][x] == "M") and genome[y+1][x] == "X" :
                        if randoo < .9:
                            genome[y][x] = "-"
                    
                    if genome[y][x] == "?" or genome[y][x] == "M":
                        if genome[y+1][x] == "X":
                            if randoo < .9:
                                genome[y][x] = "-"
                        elif genome[y+1][x] == "B":
                            if randoo < .3:
                                genome[y][x] = "-"
                    '''
               
                if(y > 14):
                    if genome[y][x] != "-" and genome[y][x] != "X" and genome[y][x] != "|" and genome[y][x] != "T":
                        genome[y][x] = "-"
                # chance to remove enemies spawned too close to mario
                if(x < 4):
                    if genome[y][x] == "E":
                        if randoo < .75:
                            genome[y][x] = "-"
                
                # remove blocks clipping into pipes        
                if genome[y][x] == "|": # or genome[y][x] == "T":
                    genome[y][x+1] = "-"
                if genome[y][x] == "T": # or genome[y][x] == "T":
                    genome[y][x+1] = "-"                     
                            
        return genome

    # Create zero or more children from self and other
    def generate_children(self, other):
        genome = copy.deepcopy(self.genome)
        other_genome = copy.deepcopy(other.genome)
        # Leaving first and last columns alone...
        # do crossover with other
        left = 1
        right = width - 1
        #for y in range(height):
        #    for x in range((int)(random.random()*right), right):
        #            genome[y][x]=other_genome[y][x]
        pa = random.randint(1, len(self.genome) - 4) if len(self.genome) > 0 else 0 #does double-point crossover
        pb = random.randint(pa, len(other.genome) - 1) if len(other.genome) > 0 else 0
        a_part = self.genome[:pa] if len(self.genome) > 0 else []
        b_part = other.genome[pa:pb] if len(other.genome) > 0 else []
        c_part= self.genome[pb:] if len(self.genome) > 0 else []
        genome= a_part+b_part+c_part
                # STUDENT Which one should you take?  Self, or other?  Why?
                # STUDENT consider putting more constraints on this to prevent pipes in the air, etc
        # do mutation; note we're returning a one-element tuple here
        #new_genome=genome
        #return (Individual_Grid(new_genome),)
        returnThisGenome = self.mutate(genome)
        return (Individual_Grid(returnThisGenome),)

    # Turn the genome into a level string (easy for this genome)
    def to_level(self):
        return self.genome

    # These both start with every floor tile filled with Xs
    # STUDENT Feel free to change these
    @classmethod
    def empty_individual(cls):
        g = [["-" for col in range(width)] for row in range(height)]
        g[15][:] = ["X"] * width
        g[14][0] = "m"
        g[7][-2] = "v"
        for col in range(8, 14):
            g[col][-2] = "f"
        for col in range(14, 16):
            g[col][-2] = "X"
        return cls(g)

    @classmethod
    def random_individual(cls):
        # STUDENT consider putting more constraints on this to prevent pipes in the air, etc
        # STUDENT also consider weighting the different tile types so it's not uniformly random
        g = [random.choices(options, k=width) for row in range(height)]
        g[15][:] = ["X"] * width
        for i in range(0,14):
            g[i][0]="-"
        for i in range(0,15):
            if i<8:
                for j in range(0, width-1):
                    if random.random()<.85:
                        g[i][j]="-"
            else:
                for j in range(0, width-1):
                    if random.random()<.6:
                        g[i][j]="-"
        
        g[7][-2] = "v"
        g[7][-1] = "-"
        for i in range(0,15):
            if i<7:
                g[i][-1]="-"
                g[i][-2]="-"
            elif i>7:
                g[i][-1] = "-"
                g[i][-2] = "f"
        
        #g[14:16][-1] = ["X", "X"]
        g[14][0] = "m"
        return cls(g)


def offset_by_upto(val, variance, min=None, max=None):
    val += random.normalvariate(0, variance**0.5)
    if min is not None and val < min:
        val = min
    if max is not None and val > max:
        val = max
    return int(val)


def clip(lo, val, hi):
    if val < lo:
        return lo
    if val > hi:
        return hi
    return val

# Inspired by https://www.researchgate.net/profile/Philippe_Pasquier/publication/220867545_Towards_a_Generic_Framework_for_Automated_Video_Game_Level_Creation/links/0912f510ac2bed57d1000000.pdf


class Individual_DE(object):
    # Calculating the level isn't cheap either so we cache it too.
    __slots__ = ["genome", "_fitness", "_level"]

    # Genome is a heapq of design elements sorted by X, then type, then other parameters
    def __init__(self, genome):
        self.genome = list(genome)
        heapq.heapify(self.genome)
        self._fitness = None
        self._level = None

    # Calculate and cache fitness
    def calculate_fitness(self):
        measurements = metrics.metrics(self.to_level())
        # Default fitness function: Just some arbitrary combination of a few criteria.  Is it good?  Who knows?
        # STUDENT Add more metrics?
        # STUDENT Improve this with any code you like
        coefficients = dict(
            meaningfulJumpVariance=0.7,
            negativeSpace=0.8,
            pathPercentage=0.5,
            emptyPercentage=0.6,
            linearity=-4.75,
            solvability=4.0
        )
        penalties = 0
        # STUDENT For example, too many stairs are unaesthetic.  Let's penalize that
        if len(list(filter(lambda de: de[1] == "6_stairs", self.genome))) > 5:
            penalties -= 2
        # STUDENT If you go for the FI-2POP extra credit, you can put constraint calculation in here too and cache it in a new entry in __slots__.
        self._fitness = sum(map(lambda m: coefficients[m] * measurements[m],
                                coefficients)) + penalties
        return self

    def fitness(self):
        if self._fitness is None:
            self.calculate_fitness()
        return self._fitness

    def mutate(self, new_genome):
        # STUDENT How does this work?  Explain it in your writeup.
        # STUDENT consider putting more constraints on this, to prevent generating weird things
        if random.random() < .075: #mutate can actually generate things
                de_type=random.choice(["4_block","5_qblock","3_coin","7_pipe", "0_hole","6_stairs","1_platform","2_enemy"])
                if de_type in ["4_block", "5_qblock"]:
                    new_de = (random.randint(1, width - 2), de_type, random.randint(0, height - 1), random.choice([True, False]))
                elif de_type ==  "3_coin":
                    new_de = (random.randint(1, width - 2), de_type, random.randint(0, height - 1))
                elif de_type == "7_pipe":
                    new_de = (random.randint(1, width - 2), de_type, random.randint(2, height - 9))
                elif de_type == "6_stairs":
                    new_de = (random.randint(1, width - 2), de_type, random.randint(1, height - 4), random.choice([-1, 1]))
                elif de_type == "0_hole":
                    new_de = (random.randint(1, width - 2), de_type, random.randint(1, 4))
                elif de_type == "1_platform":
                    new_de = (random.randint(1, width - 2), de_type, random.randint(1, 8), random.randint(0, height - 1), random.choice(["?", "X", "B"]))
                elif de_type == "2_enemy":
                    new_de = (random.randint(1, width - 2), "2_enemy")
                if len(new_genome)> 75:
                    new_genome.pop()
                heapq.heappush(new_genome, new_de)
        if random.random() < 0.1 and len(new_genome) > 0:
            to_change = random.randint(0, len(new_genome) - 1)
            de = new_genome[to_change]
            new_de = de
            x = de[0]
            de_type = de[1]
            choice = random.random()
            if de_type == "4_block":
                y = de[2]
                breakable = de[3]
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                else:
                    breakable = not de[3]
                new_de = (x, de_type, y, breakable)
            elif de_type == "5_qblock":
                y = de[2]
                has_powerup = de[3]  # boolean
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                else:
                    has_powerup = not de[3]
                new_de = (x, de_type, y, has_powerup)
            elif de_type == "3_coin":
                y = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    y = offset_by_upto(y, height / 2, min=0, max=height - 1)
                new_de = (x, de_type, y)
            elif de_type == "7_pipe":
                h = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    h = offset_by_upto(h, 2, min=2, max=height - 4)
                new_de = (x, de_type, h)
            elif de_type == "0_hole":
                w = de[2]
                if choice < 0.5:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                else:
                    w = offset_by_upto(w, 4, min=1, max=width - 2)
                new_de = (x, de_type, w)
            elif de_type == "6_stairs":
                h = de[2]
                dx = de[3]  # -1 or 1
                if choice < 0.33:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.66:
                    h = offset_by_upto(h, 8, min=1, max=height - 4)
                else:
                    dx = -dx
                new_de = (x, de_type, h, dx)
            elif de_type == "1_platform":
                w = de[2]
                y = de[3]
                madeof = de[4]  # from "?", "X", "B"
                if choice < 0.25:
                    x = offset_by_upto(x, width / 8, min=1, max=width - 2)
                elif choice < 0.5:
                    w = offset_by_upto(w, 8, min=1, max=width - 2)
                elif choice < 0.75:
                    y = offset_by_upto(y, height, min=0, max=height - 1)
                else:
                    madeof = random.choice(["?", "X", "B"])
                new_de = (x, de_type, w, y, madeof)
            elif de_type == "2_enemy":
                pass
            
            if random.random() < .01: #random chance to delete a block
                new_genome.pop(to_change)
            heapq.heappush(new_genome, new_de)
        return new_genome

    def generate_children(self, other):
        # STUDENT How does this work?  Explain it in your writeup.
        pa = random.randint(0, len(self.genome) - 1) if len(self.genome) > 0 else 0
        pb = random.randint(0, len(other.genome) - 1) if len(other.genome) > 0 else 0
        a_part = self.genome[:pa] if len(self.genome) > 0 else []
        b_part = other.genome[pb:] if len(other.genome) > 0 else []
        ga = a_part + b_part
        b_part = other.genome[:pb] if len(other.genome) > 0 else []
        a_part = self.genome[pa:] if len(self.genome) > 0 else []
        gb = b_part + a_part
        # do mutation
        return Individual_DE(self.mutate(ga)), Individual_DE(self.mutate(gb))

    # Apply the DEs to a base level.
    def to_level(self):
        if self._level is None:
            base = Individual_Grid.empty_individual().to_level()
            for de in sorted(self.genome, key=lambda de: (de[1], de[0], de)):
                # de: x, type, ...
                x = de[0]
                de_type = de[1]
                if de_type == "4_block":
                    y = de[2]
                    breakable = de[3]
                    base[y][x] = "B" if breakable else "X"
                elif de_type == "5_qblock":
                    y = de[2]
                    has_powerup = de[3]  # boolean
                    base[y][x] = "M" if has_powerup else "?"
                elif de_type == "3_coin":
                    y = de[2]
                    base[y][x] = "o"
                elif de_type == "7_pipe":
                    h = de[2]
                    base[height - h - 1][x] = "T"
                    for y in range(height - h, height):
                        base[y][x] = "|"
                elif de_type == "0_hole":
                    w = de[2]
                    for x2 in range(w):
                        base[height - 1][clip(1, x + x2, width - 2)] = "-"
                elif de_type == "6_stairs":
                    h = de[2]
                    dx = de[3]  # -1 or 1
                    for x2 in range(1, h + 1):
                        for y in range(x2 if dx == 1 else h - x2):
                            base[clip(0, height - y - 1, height - 1)][clip(1, x + x2, width - 2)] = "X"
                elif de_type == "1_platform":
                    w = de[2]
                    h = de[3]
                    madeof = de[4]  # from "?", "X", "B"
                    for x2 in range(w):
                        base[clip(0, height - h - 1, height - 1)][clip(1, x + x2, width - 2)] = madeof
                elif de_type == "2_enemy":
                    base[height - 2][x] = "E"
            self._level = base
        return self._level

    @classmethod
    def empty_individual(_cls):
        # STUDENT Maybe enhance this
        g = []
        return Individual_DE(g)

    @classmethod
    def random_individual(_cls):
        # STUDENT Maybe enhance this
        elt_count = random.randint(8, 128)
        g = [random.choice([
            (random.randint(1, width - 2), "0_hole", random.randint(1, 8)),
            (random.randint(1, width - 2), "1_platform", random.randint(1, 8), random.randint(0, height - 1), random.choice(["?", "X", "B"])),
            (random.randint(1, width - 2), "2_enemy"),
            (random.randint(1, width - 2), "3_coin", random.randint(0, height - 1)),
            (random.randint(1, width - 2), "4_block", random.randint(0, height - 1), random.choice([True, False])),
            (random.randint(1, width - 2), "5_qblock", random.randint(0, height - 1), random.choice([True, False])),
            (random.randint(1, width - 2), "6_stairs", random.randint(1, height - 4), random.choice([-1, 1])),
            (random.randint(1, width - 2), "7_pipe", random.randint(2, height - 4)),
             (random.randint(1, width - 2), "7_pipe", random.randint(2, height - 4))
        ]) for i in range(elt_count)]
        return Individual_DE(g)


#Individual = Individual_DE
Individual = Individual_Grid


def generate_successors(population):
    results = []
    # STUDENT Design and implement this
    # Hint: Call generate_children() on some individuals and fill up results.

    poplist = sorted(population, key=lambda level: level.fitness(),reverse=True)

    for i in range(6): #elitist, strongest gets passed on without children
        results.append(poplist[i])

    for i in range((int)(len(poplist)/1.25)): # this takes about 80% of the population, not all will move on
        if random.random() < 1-(i*.005): #tournament, individuals get passed on with chance proportional to fitness
            newChild=poplist[i].generate_children(poplist[i+1]) #make children with the one right below in fitness
            results.append(newChild[0])

    
    #this process takes about 60% of the population, including 5 strongest
    return results


def ga():
    # STUDENT Feel free to play with this parameter
    pop_limit = 480
    # Code to parallelize some computations
    batches = os.cpu_count()
    if pop_limit % batches != 0:
        print("It's ideal if pop_limit divides evenly into " + str(batches) + " batches.")
    batch_size = int(math.ceil(pop_limit / batches))
    with mpool.Pool(processes=os.cpu_count()) as pool:
        init_time = time.time()
        # STUDENT (Optional) change population initialization
        population = [Individual.random_individual() if random.random() < 1.0
                      else Individual.empty_individual()
                      for _g in range(pop_limit)]
        # But leave this line alone; we have to reassign to population because we get a new population that has more cached stuff in it.
        population = pool.map(Individual.calculate_fitness,
                              population,
                              batch_size)
        init_done = time.time()
        print("Created and calculated initial population statistics in:", init_done - init_time, "seconds")
        generation = 0
        start = time.time()
        now = start
        print("Use ctrl-c to terminate this loop manually.")
        try:
            while True:
                now = time.time()
                # Print out statistics
                if generation > 0:
                    best = max(population, key=Individual.fitness)
                    print("Generation:", str(generation))
                    print("Max fitness:", str(best.fitness()))
                    print("Average generation time:", (now - start) / generation)
                    print("Net time:", now - start)
                    with open("levels/last.txt", 'w') as f:
                        for row in best.to_level():
                            f.write("".join(row) + "\n")
                generation += 1
                # STUDENT Determine stopping condition
                stop_condition = False
                if stop_condition or generation > 10:
                    break
                # STUDENT Also consider using FI-2POP as in the Sorenson & Pasquier paper
                gentime = time.time()
                next_population = generate_successors(population)
                gendone = time.time()
                print("Generated successors in:", gendone - gentime, "seconds")
                # Calculate fitness in batches in parallel
                next_population = pool.map(Individual.calculate_fitness,
                                           next_population,
                                           batch_size)
                popdone = time.time()
                print("Calculated fitnesses in:", popdone - gendone, "seconds")
                population = next_population
        except KeyboardInterrupt:
            pass
    return population


if __name__ == "__main__":
    final_gen = sorted(ga(), key=Individual.fitness, reverse=True)
    best = final_gen[0]
    print("Best fitness: " + str(best.fitness()))
    now = time.strftime("%m_%d_%H_%M_%S")
    # STUDENT You can change this if you want to blast out the whole generation, or ten random samples, or...
    for k in range(0, 10):
        with open("levels/" + now + "_" + str(k) + ".txt", 'w') as f:
            for row in final_gen[k].to_level():
                f.write("".join(row) + "\n")
