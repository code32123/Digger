import pygame
import pygame.locals
import sys
import os
import math
import json
import random
import copy

class block():
	id=0
	name=""
	digLvl= False
	canMove=False
	needDig=True
	canFall=False
	reward = 0
	tile = None
	spawnFreq = None
	def __init__(self,id,name,digLvl,canMove,needDig,canFall,reward,tile,spawnFreq = None):
		self.id        = id
		self.name      = name
		self.digLvl    = digLvl
		self.canMove   = canMove
		self.needDig   = needDig
		self.canFall   = canFall
		self.reward    = reward
		self.tile      = tile
		self.spawnFreq = spawnFreq
	def canDig(self):
		if self.digLvl == -1:
			return False
		return STATS["digLevel"] >= self.digLvl
	def shouldDig(self):
		return self.canMove and self.needDig and self.canDig()
	def shouldMove(self):
		return self.canMove and ((not self.needDig) or (self.needDig and self.canDig()))
	def runChances(self, height):
		h1, h2 = self.spawnFreq.height
		if h1 <= height <= h2:
			if random.random() < self.spawnFreq.chance:
				return random.randrange(*self.spawnFreq.cluster)
		return 0
				
def Layer(block, width, height):
	tempLayer = []
	for i in range(height):
		tempRow = [block]*width
		tempLayer.append(tempRow)
	return tempLayer

def genTerrain(dimensions):
	w, h = dimensions
	emptyLevel = []
	# Basic layer map: (type, height)
	# Default is one air, then 1/3 grass 2/3 stone 
	layerMap = [(a, 1), (g,round((h-1)*(1/3))), (s,round((h-1)*(2/3)))]
	for layerItem in layerMap:
		emptyLevel += Layer(layerItem[0], w, layerItem[1])

	shadowMap  = [[50 for x in range(w)] for y in range(h)]
	# Now that we have a blank map, we can fill it with ORES!!
	oreLevel = list(emptyLevel)
	for height, layer in enumerate(oreLevel):
		for column, block in enumerate(layer):
			for blockOption in Ores:
				clusterSize = blockOption.runChances(height)
				if clusterSize != 0:
					oreLevel = drawCluster(blockOption, clusterSize, oreLevel, height, column)
				
	return oreLevel, shadowMap

def drawCluster(block, volume, levelMap, height, column):
	x, y = column, height
	for i in range(volume):
		# Note which block is being overwritten so that the ores can blend
		# with the texture
		blockTemp = copy.copy(block)
		#blockTemp.tile.imitate = levelMap[y][x]
		try:
			levelMap[y][x] = blockTemp
		except:
			pass
		# Move in a random direction (Including Diagnols and no move)
		x += random.choice([-1, 0, 1])
		y += random.choice([-1, 0, 1])
	return levelMap

def getStringKey(column,row,matches):
	up    = str(int(getLvl(column,row-1) in matches))
	right = str(int(getLvl(column+1,row) in matches))
	down  = str(int(getLvl(column,row+1) in matches))
	left  = str(int(getLvl(column-1,row) in matches))
	return up+right+down+left

def darken(surface, value):
	black = pygame.Surface((16,16))
	black.fill((int(Dead)*80,0,0))
	surface.set_alpha(value)
	black.blit(surface, (0,0))
	return black
	
def distance(p1, p2):
	return (p2[0]-p1[0])**2 + (p2[1]-p1[1])**2

def getLvl(x, y, lvlD=None, fallback=None):
	fallback = v if fallback == None else fallback
	if lvlD == None:
		workingData = levelData
	else:
		workingData = lvlD
	if y<0:
		return fallback
	try:
		totalWidth = len(workingData[y])
		while x <= 0:
			x += totalWidth
		x %= totalWidth
		return workingData[y][x]
	except IndexError:
		return fallback

def setLvl(x, y, val, lvlD=None):
	if lvlD == None:
		workingData = levelData
	else:
		workingData = lvlD
	totalWidth = len(workingData[y])
	while x <= 0:
		x += totalWidth
	x %= totalWidth
	if lvlD == None:
		levelData[y][x] = val
	else:
		lvlD[y][x] = val
		return lvlD
	

class tile():
	folder = ""
	name=""
	images = {}
	isMulti=False
	matches=[]
	def __init__(self, folder, name, BlockType="Block",matches=[]):
		self.folder = folder
		self.name = name
		self.images = {}
		self.matches = matches
		self.isMulti = os.path.isdir(os.path.join(folder, name))

		if not self.isMulti:
			fullPath = os.path.join(folder, name) + ".png"
			if BlockType=="Tile":
				self.images = pygame.transform.scale(pygame.image.load(fullPath), (16, 16)).convert_alpha()
			else:
				self.images = pygame.transform.scale(pygame.image.load(fullPath), (16, 16)).convert()
			isMulti = True
		else:
			for fileName in os.listdir(os.path.join(folder, name)):
				fullPath = os.path.join(folder, name, fileName)
				self.images[fileName.split(".")[0]] = pygame.transform.scale(pygame.image.load(fullPath), (16, 16)).convert()
					
					
	def pick(self,x,y):
		pickT((x,y))
	def pickT(self,T):
		x,y = T
		if self.isMulti:
			stringKey = getStringKey(x,y,self.matches)
			return self.images[stringKey]
		else:
			return self.images

class SpawnFrequencies:
	cluster, height, chance = 0, 0, 0
	def __init__(self, cluster, height, chance):
		self.cluster = cluster
		self.height  = height
		self.chance  = chance



# Player Statistics
STATS = {
	"digLevel"     :1,
	"canLadder"    :True,
	"surviveFalls" :1,
	"viewDistance" :5,
	"fullBattery"  :10,
}


# Init game vairables
pX = 0
pY = 0
score=0
tileSize = 16
width, height = 20, 20
offsetToCenter = tileSize*((width-1)/2),16*9.5
Level_Width, Level_Height = 100, 100
debugPrints = False
movementCurve = [16,15,13,10,6,3,1,0]
Dead    = False
Battery = STATS["fullBattery"]

# PyGame Variables
pygame.init()
Player    = [pygame.transform.scale(pygame.image.load("Res/Player/" + str(x) + ".png"), (16, 16)) for x in range(8)]
screen    = pygame.display.set_mode((16*width, 16*height), pygame.RESIZABLE)
MyFont    = pygame.font.Font("AnonymousMod.ttf", 16)
# SmallFont = pygame.font.Font("AnonymousMod.ttf", 16)

# block:(id,name,digLvl,canMove,needDig,canFall,reward,
#   tile:(Folder,Name,Type=None),
#   SpawnFreq:(Cluster,Height,Chance)=None
# )
v = block(-1,"Void",  -1,False,False,False,0,tile("Res","Air"  ))
a = block( 0,"Air",   -1,True, False,True, 0,tile("Res","Air"  ))
g = block( 1,"Grass",  1,True, True, False,0,tile("Res","Grass"))
s = block( 2,"Stone",  2,True, True, False,0,tile("Res","Stone"))
l = block( 3,"Ladder",-1,True, False,False,0,tile("Res","Ladder","Tile"))
C = block( 4,"Coal",   1,True, True, False,1,tile("Res/Ores","Coal" ),
      SpawnFrequencies((1,2), ( 0,20), 4/(16**2)))
I = block( 5,"Iron",   1,True, True, False,2,tile("Res/Ores","Iron" ),
      SpawnFrequencies((2,4), (22,30), 5/(20**2)))
G = block( 6,"Gold",   1,True, True, False,4,tile("Res/Ores","Gold" ),
      SpawnFrequencies((3,4), (28,50), 3/(16**2)))
L = block( 7,"Lux",    1,True, True, False,6,tile("Res/Ores","Lux"  ),
      SpawnFrequencies((1,2), (40,80), 2/(10**2)))

# List all blocks for later reference
Ores = [C,I,G,L]
blocks = [v,a,g,s,l] + Ores


# Set default tile matches
g.tile.matches = [g, s] + Ores
s.tile.matches = [s]

# Make ladder transparent over air
airCopy = a.tile.images.copy()
airCopy.blit(l.tile.images,(0,0))
l.tile.images = airCopy

# Use blocks defined above to generate terrain
levelData, shadowData = genTerrain((Level_Width,Level_Height))

# Counters
frame = 0
AnimList = []
falling = 0

# Main GameLoop
while True:
	while pX < 0:
		pX += Level_Width
	pX %= Level_Width
		
	if frame%2==0:
		if len(AnimList) != 0:
			# Basically, pops the next animation transform and applies it.
			tempOffset = (offsetToCenter[0] + AnimList[0][0], offsetToCenter[1] + AnimList[0][1])
			animOffset = AnimList[0]
			AnimList = AnimList[1:]
		else:
			tempOffset = offsetToCenter
			animOffset = [0,0]
		screen.fill((180, 200, 255))
		
		for y in range(-2,height+2):
			for x in range(-2,width+2):
				tileToPlace = (x+pX-int(offsetToCenter[0]//16)-1, y+pY-int(offsetToCenter[1]//16)-1)
				block = getLvl(*tileToPlace)
				
				placePos = (((x-0.5)*16)+animOffset[0],((y-0.5)*16)+animOffset[1])
				dist = math.sqrt(distance((pX, pY), tileToPlace))
				PlayerEmitLight = dist < STATS["viewDistance"]
				#print(tileToPlace, PlayerEmitLight)
				if PlayerEmitLight and tileToPlace[1] >= 0 and tileToPlace[1] < Level_Height:
					setLvl(*tileToPlace, 200, shadowData)

					
				darkness = getLvl(*tileToPlace, shadowData, fallback=255) if not Dead else 10
				
				normal = block.tile.pickT(tileToPlace)
				dark = darken(normal, darkness)
				screen.blit(dark, placePos)
				
		if getLvl(pX,pY+1) in [bl for bl in blocks if bl.canFall]:
			pY+=1
			AnimList = [[0,y] for y in movementCurve]
			falling +=1
		else:
			if falling > STATS["surviveFalls"]:
				Dead = True
			falling = 0
		if Battery <= 0:
			Dead = True
		scoreImg = MyFont.render(str(score) + "$", True, (255,255,0))
		screen.blit(scoreImg, (10,10))
		if debugPrints:
			debugList = json.dumps(STATS, indent=0).split("\n")
			for i, item in enumerate(debugList[1:-1]):
				scoreImg = MyFont.render(item, True, (255,255,255))
				screen.blit(scoreImg, (10,26+(i*15)))
		if Dead:
			deathImg1 = MyFont.render("  - Press Space -  ", True, (255,0,0))
			deathImg2 = MyFont.render("to Return to Surface", True, (255,0,0))
			screen.blit(deathImg1, (60,(height*16)-32))
			screen.blit(deathImg2, (50,(height*16)-16))
		
		battRatio = Battery/STATS["fullBattery"]
		if battRatio >= (7/7):
			screen.blit(Player[7], (offsetToCenter))
		elif battRatio >= (6/7):
			screen.blit(Player[6], (offsetToCenter))
		elif battRatio >= (5/7):
			screen.blit(Player[5], (offsetToCenter))
		elif battRatio >= (4/7):
			screen.blit(Player[4], (offsetToCenter))
		elif battRatio >= (3/7):
			screen.blit(Player[3], (offsetToCenter))
		elif battRatio >= (2/7):
			screen.blit(Player[2], (offsetToCenter))
		elif battRatio >= (1/7):
			screen.blit(Player[1], (offsetToCenter))
		else:
			screen.blit(Player[0], (offsetToCenter))
		
	pygame.display.update()
	events = pygame.event.get()
	for event in events:
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_SPACE and Dead:
				 pX, pY = 0,0
				 Dead = False
				 Battery = STATS["fullBattery"]
			if event.key == pygame.K_LEFT and not Dead:
				bl = getLvl(pX-1, pY)
				if bl.shouldDig():
					score += bl.reward
					setLvl(pX-1, pY, a)
				if bl.shouldMove():
					pX -= 1
					Battery -= 1
					AnimList = [[-x,0] for x in movementCurve]
			if event.key == pygame.K_RIGHT and not Dead:
				bl = getLvl(pX+1, pY)
				if bl.shouldDig():
					score += bl.reward
					setLvl(pX+1, pY, a)
				if bl.shouldMove():
					pX += 1
					Battery -= 1
					AnimList = [[x,0] for x in movementCurve]
			if event.key == pygame.K_UP and not Dead:
				bl = getLvl(pX, pY-1)
				if bl.shouldDig():
					score += bl.reward
					setLvl(pX, pY-1, a)
				if bl.shouldMove():
					if STATS["canLadder"]:
						setLvl(pX, pY, l)
					pY -= 1
					Battery -= 1
					AnimList = [[0,-y] for y in movementCurve]
			if event.key == pygame.K_DOWN and not Dead:
				bl = getLvl(pX, pY+1)
				falling += 1
				if bl.shouldDig():
					score += bl.reward
					setLvl(pX, pY+1, a)
				if bl.shouldMove():
					pY += 1
					Battery -= 1
					AnimList = [[0,y] for y in movementCurve]
					
			if event.key == pygame.K_p:
				STATS["digLevel"] += 1
				debugPrints = True
			if event.key == pygame.K_o:
				STATS["digLevel"] -= 1
				debugPrints = True
			if event.key == pygame.K_i:
				STATS["viewDistance"] += 1
				debugPrints = True
			if event.key == pygame.K_u:
				STATS["viewDistance"] -= 1
				debugPrints = True
			if event.key == pygame.K_k:
				STATS["surviveFalls"] += 1
				debugPrints = True
			if event.key == pygame.K_j:
				STATS["surviveFalls"] -= 1
				debugPrints = True
			if event.key == pygame.K_l:
				STATS["canLadder"] = not STATS["canLadder"]
				debugPrints = True
			if event.key == pygame.K_b:
				 STATS["fullBattery"] = 10000
				 Battery = STATS["fullBattery"]
				 debugPrints = True
			if event.key == pygame.K_SLASH:
				exec(input("/>>> "))
	frame += 1

# If it exits, just print 'Died'
print("Died")