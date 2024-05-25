import badger2040
import badger_os
import jpegdec
import os
import random
import time

# Global Constants
DEBUG_INPUTS = False

WIDTH = badger2040.WIDTH
HEIGHT = badger2040.HEIGHT
VERSION = "v0.7.1"
GAME_NAME = "BADGER DUNGEON"

PADDING = 2

MAX_HEALTH = 100

IMAGE_WIDTH = 64

SHOP_ATTACK_ADDITION = 3                                                      
SHOP_DEFENSE_ADDITION = 1
SHOP_HEALING_ADDITION = 5

COMBAT_END_GOLD_MULTIPLIER = 1.5

MONSTER_ATTACK_LEVEL_MULTIPLIER = 5
MONSTER_DEFENSE_LEVEL_MULTIPLIER = 1.5
# ------------------------------
#      Utility functions
# ------------------------------

def default_state():
    return {
    "health": MAX_HEALTH,
    "attack": 34,
    "defense": 2,
    "healing": 20,
    "floor": 1,
    "gold": 5,
    # Floor Layout: [E]ntry, [T]reasure, [M]onster, [S]tairs, [N]othing.
    "layout": gen_floor(1),
    "location": 0,
    "state": "Title", # Title, Shop, Room, Combat, Dead
    "monster": gen_monster(1),
    "combat": {
        "select": 0,
        "multiplier": 1,
    },
    "shop": {
        "select": 0,
        "weaponCost": 5,
        "armorCost": 5,
        "potionCost": 5,
        "actionMessage": ""
    }
}

def gen_monster(level):
    return {
    "name": "Monster",
    "fileName": None,
    "level": level,
    "health": 100,
    "attack": 10, # Calculated when parsing the file in calc_monster_attack
    "defense": 1,
    "message": "is looking for a fight",
    "ratio": [4, 3, 3],
    "floors": [1, 9999],
}

def gen_floor_room(id, type, northRoom, eastRoom, southRoom, westRoom):
    # Floor Layout: [E]ntry, [T]reasure, [M]onster, [S]tairs, [N]othing.
    return {
        "id": id,
        "type": type,
        "cleared": False,
        "n": northRoom,
        "e": eastRoom,
        "s": southRoom,
        "w": westRoom,
    }
    

def gen_floor(floorLevel):
    # Floor Layout: [E]ntry, [T]reasure, [M]onster, [S]tairs, [N]othing.
    if floorLevel == 1:
        return [
            gen_floor_room(0, "E", 1, -1, -1, -1),
            gen_floor_room(1, "M", 2, 4, 0, -1),
            {
            "id": 2,
            "type": "T",
            "cleared": False,
            "n": 3,
            "e": -1,
            "s": 1,
            "w": -1
            },
            {
            "id": 3,
            "type": "S",
            "cleared": False,
            "n": -1,
            "e": -1,
            "s": 2,
            "w": -1
            },
            {
            "id": 4,
            "type": "N",
            "cleared": False,
            "n": -1,
            "e": -1,
            "s": -1,
            "w": 1
            },
        ]
    
    # Gen code
    
    rooms = [
        gen_floor_room(0, "E", -1, -1, -1, -1),
    ]
    
    roomId = 1
    prevMainRoomId = 0
    mainPathCount = 3 + floorLevel;
    
    roomPools =  {
      "M": floorLevel,
      "T": floorLevel,
    }
    
    roomDirection = random.randint(0, 3)
    
    for x in range(mainPathCount):
        
        roomType = "N"
        if x == mainPathCount - 1:
            # add exit
            roomType = "S"
        else:
            roomType = select_room_type(roomPools)
            if roomType != "N":
                roomPools[roomType] -= 1
        
        rooms.append(gen_floor_room(roomId, roomType, -1, -1, -1, -1))
        mainRoomId = roomId
        
        prevRoomDirection = roomDirection
        
        roomAttachN = -1
        roomAttachE = -1
        roomAttachS = -1
        roomAttachW = -1
        if roomDirection == 0:
            roomAttachN = prevMainRoomId
            roomDirection += random.randint(-1, 1)
            if roomDirection == -1:
                roomDirection = 3
        elif roomDirection == 1:
            roomAttachE = prevMainRoomId
            roomDirection += random.randint(-1, 1)
        elif roomDirection == 2:
            roomAttachS = prevMainRoomId
            roomDirection += random.randint(-1, 1)
        elif roomDirection == 3:
            roomAttachW = prevMainRoomId
            roomDirection += random.randint(-1, 1)
            roomDirection %= 4
        
        #attach_room(rooms, mainRoomId,  roomAttachN, roomAttachE, roomAttachS, roomAttachW)
        #debug_print_room(mainRoomId, roomType, roomDirection, roomAttachN, roomAttachE, roomAttachS, roomAttachW)
        roomId += 1
        
        # make room offshoot
        if random.randint(0, mainPathCount) <= x:
            subRoomType = select_room_type(roomPools)
            if subRoomType != "N":
                roomPools[subRoomType] -= 1
            rooms.append(gen_floor_room(roomId, subRoomType, -1, -1, -1, -1))
            subRoomAttachN = -1
            subRoomAttachE = -1
            subRoomAttachS = -1
            subRoomAttachW = -1
            if roomAttachN == -1 and prevRoomDirection != 0:
                roomAttachN = roomId
                subRoomAttachS = mainRoomId
            elif roomAttachE == -1 and prevRoomDirection != 1:
                roomAttachE = roomId
                subRoomAttachW = mainRoomId
            elif roomAttachS == -1 and prevRoomDirection != 2:
                roomAttachS = roomId
                subRoomAttachN = mainRoomId
            elif roomAttachW == -1 and prevRoomDirection != 3:
                roomAttachW = roomId
                subRoomAttachE = mainRoomId
            debug_print_room(roomId, subRoomType, -1, subRoomAttachN, subRoomAttachE, subRoomAttachS, subRoomAttachW)
            roomId += 1
        
        debug_print_room(mainRoomId, roomType, roomDirection, roomAttachN, roomAttachE, roomAttachS, roomAttachW)

        attach_room(rooms, mainRoomId,  roomAttachN, roomAttachE, roomAttachS, roomAttachW)
        prevMainRoomId = mainRoomId

    return rooms

def debug_print_room(roomId, roomType, roomDirection, roomAttachN, roomAttachE, roomAttachS, roomAttachW):
    if DEBUG_INPUTS:
            print(f'{roomId} {roomType}: room direction: {roomDirection} - Connections: {roomAttachN}, {roomAttachE}, {roomAttachS}, {roomAttachW}')
            
def select_room_type(roomPools):
    
    select = random.randint(1, 10)
    
    if select <= 4 and roomPools["M"] > 0:
        return "M"
    if select <= 7 and roomPools["T"] > 0:
        return "T"

    return "N"

def attach_room(rooms, roomId, linkNorthRoomId, linkEastRoomId, linkSouthRoomId, linkWestRoomId):
    rooms[roomId]["n"] = linkNorthRoomId;
    if linkNorthRoomId != -1:
        rooms[linkNorthRoomId]["s"] = roomId
        
    rooms[roomId]["e"] = linkEastRoomId;
    if linkEastRoomId != -1:
        rooms[linkEastRoomId]["w"] = roomId
    
    rooms[roomId]["s"] = linkSouthRoomId;
    if linkSouthRoomId != -1:
        rooms[linkSouthRoomId]["n"] = roomId
        
    rooms[roomId]["w"] = linkWestRoomId;
    if linkWestRoomId != -1:
        rooms[linkWestRoomId]["e"] = roomId

# ------------------------------
#      Drawing functions
# ------------------------------

# Draw the dungeon
def draw_dungeon(stateName):
    display.set_pen(15)
    display.clear()

    # Uncomment this if a white background is wanted behind the company
    # display.set_pen(15)
    # display.rectangle(1, 1, TEXT_WIDTH, COMPANY_HEIGHT - 1)
    
    
    if stateName == "Title":
         draw_title()
    elif stateName == "Dead":
         draw_dead(state["floor"])
    elif stateName == "Shop":
         draw_shop()
    elif stateName == "Room":
         draw_map()
    elif stateName == "Combat":
         draw_combat()
    else:
        # Make unknown
        draw_unknown(stateName)
    
    display.update()
    
def draw_title():
    # Draw the title screen
    display.set_pen(0)  # Change this to 0 if a white background is used
    display.set_font("serif")
    display.text(GAME_NAME, PADDING, PADDING + 15, scale=0.99)
    display.text(VERSION, PADDING + (WIDTH // 2) - 25, 40 + PADDING, scale=0.6)

    display.set_font("bitmap8")
    display.text("start", PADDING + (WIDTH // 2) - 18, HEIGHT - 20)
    
def draw_combat():
    
    floor = state["floor"]
    health = state["health"]
    healthMax = MAX_HEALTH
    attack = state["attack"]
    defense = state["defense"]
    
    monster = state["monster"]
    monsterHealthMax = MAX_HEALTH
        
    # Draw the title screen
    display.set_pen(0)  # Change this to 0 if a white background is used
    display.set_font("sans")
    display.text(f'lv:{monster["level"]:2} {monster["name"]}', PADDING, PADDING + 5, scale=0.5)
    display.text(f'{monster["health"]:3}/{monsterHealthMax:3}', PADDING, PADDING + 22, scale=0.4)
    
    display.set_font("bitmap8")
    display.text(f'{monster["name"]} {monster["message"]}', WIDTH - PADDING - 150, 74, wordwrap=120, scale=0.4)

    display.set_pen(6)
    # temp mob image
    #display.rectangle(40, PADDING + 30, 64, 64)
    
    badge_image = "/dungeon1/monster/example.jpg"

    if monster["fileName"] is not None:
        badge_image = f'/dungeon1/monster/{monster["fileName"]}.jpg'
        
    # Draw monster image
    jpeg.open_file(badge_image)
    jpeg.decode(40, PADDING + 30, 0)
    
    draw_stats_and_buttons(floor, health, healthMax, attack, defense);
    
    draw_combat_menu(state)
    
def draw_combat_menu(state):
    
    widthOffset = 150
    heightOffset = PADDING + 5
    heightGap = 18
    textScale = 0.5
    
    options = ["Attack", "Block", "Heavy Atk", "Potion"]
    selectedIndex = state["combat"]["select"]
    
    display.set_font("sans")

    # Draw options
    for i in range(len(options)):
        display.set_pen(0)

        # do something with options[i]
        if i == selectedIndex:
            display.rectangle(WIDTH - PADDING - widthOffset, heightOffset + (heightGap * i) - 6, 120, 16)
            display.set_pen(15)
            
        display.text(options[i], WIDTH - PADDING - widthOffset, heightOffset + (heightGap * i), scale=textScale)

    display.set_pen(2)
    display.line(WIDTH - PADDING - widthOffset - 2, 0, WIDTH - PADDING - widthOffset - 2, heightOffset + (heightGap * 3) + 8)
    display.line(WIDTH - PADDING - widthOffset - 2, heightOffset + (heightGap * 3) + 8, WIDTH - PADDING - 12, heightOffset + (heightGap * 3) + 8)

def draw_shop():
    
    floor = state["floor"]
    health = state["health"]
    healthMax = MAX_HEALTH
    attack = state["attack"]
    defense = state["defense"]
    gold = state["gold"]
    
    shop = state["shop"]
    shopSelect = shop["select"]
    
    monster = state["monster"]
    monsterHealthMax = MAX_HEALTH
        
    # Draw shop info
    display.set_pen(0)  # Change this to 0 if a white background is used
    display.set_font("sans")
    display.text(f'Shop, Floor {floor:2}', PADDING, PADDING + 5, scale=0.5)
    display.text(f'Gold:{gold:3}', PADDING, PADDING + 22, scale=0.4)
    
    costMessage = ""
    if shopSelect == 0:
        costMessage = f'Weapon Cost: {shop["weaponCost"]}.'
    elif shopSelect == 1:
        costMessage = f'Armor Cost: {shop["armorCost"]}.'
    elif shopSelect == 2:
        costMessage = f'Potion Cost: {shop["potionCost"]}.'
    
    display.set_font("bitmap8")
    display.text(f'{costMessage} {shop["actionMessage"]}', WIDTH - PADDING - 150, 74, wordwrap=120, scale=0.4)

    # Draw shop keeper image
    badge_image = "/dungeon1/shopkeep.jpg"
    jpeg.open_file(badge_image)
    jpeg.decode(40, PADDING + 30, 0)
    
    draw_stats_and_buttons(floor, health, healthMax, attack, defense);
    
    draw_shop_menu(state)

def draw_shop_menu(state):
    
    widthOffset = 150
    heightOffset = PADDING + 5
    heightGap = 18
    textScale = 0.5
    
    options = ["Weapon", "Armor", "Potion", "Leave"]
    selectedIndex = state["shop"]["select"]
    
    display.set_font("sans")

    # Draw options
    for i in range(len(options)):
        display.set_pen(0)

        # do something with options[i]
        if i == selectedIndex:
            display.rectangle(WIDTH - PADDING - widthOffset, heightOffset + (heightGap * i) - 6, 120, 16)
            display.set_pen(15)
            
        display.text(options[i], WIDTH - PADDING - widthOffset, heightOffset + (heightGap * i), scale=textScale)

    display.set_pen(2)
    display.line(WIDTH - PADDING - widthOffset - 2, 0, WIDTH - PADDING - widthOffset - 2, heightOffset + (heightGap * 3) + 8)
    display.line(WIDTH - PADDING - widthOffset - 2, heightOffset + (heightGap * 3) + 8, WIDTH - PADDING - 12, heightOffset + (heightGap * 3) + 8)
    
def draw_dead(floor):
    display.set_pen(0)
    display.clear()
    
    # Draw the dead screen
    display.set_pen(15)  # Change this to 0 if a white background is used
    display.set_font("serif")
    display.text("You died.", PADDING + (WIDTH // 2) - 50, PADDING + 15, scale=0.99)
    display.text("Go again?", PADDING + (WIDTH // 2) - 50, 40 + PADDING, scale=0.6)
    
    display.text(f"Floor {floor:2}", PADDING + (WIDTH // 2) - 50, 65 + PADDING, scale=0.5)


    display.set_font("bitmap8")
    display.text("restart", PADDING + (WIDTH // 2) - 30, HEIGHT - 20)
    
    
def draw_map():
    
    floor = state["floor"]
    health = state["health"]
    healthMax = MAX_HEALTH
    attack = state["attack"]
    defense = state["defense"]
    
    location = state["location"]
    layout = state["layout"]
    currentRoom = layout[location]
    
    print(f"Rendering room {location}")
    
    thickness = 2
    
    yOffset = -10
    
    display.set_pen(0)  # Change this to 0 if a white background is used
    display.set_font("bitmap8")
    
    draw_room(WIDTH // 2, HEIGHT // 2 + yOffset, 20, 20, 2)
    
    typeRender = currentRoom["type"]
    if currentRoom["cleared"] == True:
        if typeRender == "M":
            typeRender = "X"
        elif typeRender == "T":
            typeRender = "O"
    
    display.text(typeRender, WIDTH // 2 - 4, HEIGHT // 2 + yOffset - 6)
    
    # backward
    
    if currentRoom["s"] >= 0:
    
        draw_partial_room_bottom(WIDTH // 2, HEIGHT // 2 + 27, 20, 8, 1)
    
    # left
    
    if currentRoom["w"] >= 0:
    
        draw_room(WIDTH // 2 - 50, HEIGHT // 2 + yOffset, 20, 20, 1)
        draw_room_hall(True, WIDTH // 2 - 25, HEIGHT // 2 + yOffset)
    
    # forward
    
    if currentRoom["n"] >= 0:
    
        draw_room(WIDTH // 2, HEIGHT // 2 + yOffset - 50, 20, 20, 1)
        draw_room_hall(False, WIDTH // 2, HEIGHT // 2 + yOffset - 25)

    # right
    
    if currentRoom["e"] >= 0:

        draw_room(WIDTH // 2 + 50, HEIGHT // 2 + yOffset, 20, 20, 1)
        draw_room_hall(True, WIDTH // 2 + 25, HEIGHT // 2 + yOffset)

    
    draw_stats_and_buttons(floor, health, healthMax, attack, defense);
    
def draw_room(centerX, centerY, halfLengthX, halfLengthY, thickness):
    display.line(centerX - halfLengthX, centerY - halfLengthY, centerX + halfLengthX, centerY - halfLengthY, thickness)
    display.line(centerX - halfLengthX, centerY - halfLengthY, centerX - halfLengthX, centerY + halfLengthY, thickness)
    
    display.line(centerX + halfLengthX, centerY - halfLengthY, centerX + halfLengthX, centerY + halfLengthY, thickness)
    display.line(centerX - halfLengthX, centerY + halfLengthY, centerX + halfLengthX, centerY + halfLengthY, thickness)
    
def draw_partial_room_bottom(centerX, centerY, halfLengthX, halfLengthY, thickness):
    
    # Draw hallway
    
    hallShiftY = 13
    hallLength = 5
    
    display.line(centerX + 5, centerY - hallLength - hallShiftY, centerX + 5, centerY + hallLength - hallShiftY, thickness)
    display.line(centerX - 5, centerY - hallLength - hallShiftY, centerX - 5, centerY + hallLength - hallShiftY, thickness)

    # Draw room
    
    display.line(centerX - halfLengthX, centerY - halfLengthY, centerX + halfLengthX, centerY - halfLengthY, thickness)
    display.line(centerX - halfLengthX, centerY - halfLengthY, centerX - halfLengthX, centerY + halfLengthY, thickness)
    
    display.line(centerX + halfLengthX, centerY - halfLengthY, centerX + halfLengthX, centerY + halfLengthY, thickness)

def draw_room_hall(horizontal, centerX, centerY):
    
    hallLength = 5
    
    if horizontal:
        display.line(centerX - hallLength, centerY + 5, centerX + hallLength, centerY + 5, 1)
        display.line(centerX - hallLength, centerY - 5, centerX + hallLength, centerY - 5, 1)
    else:
        display.line(centerX + 5, centerY - hallLength, centerX + 5, centerY + hallLength, 1)
        display.line(centerX - 5, centerY - hallLength, centerX - 5, centerY + hallLength, 1)

        
def draw_unknown(stateName):
    # Draw the unkown screen
    display.set_pen(0)  # Change this to 0 if a white background is used
    display.set_font("serif")
    display.text("Unknown State: ", PADDING, PADDING + 15, scale=0.99)
    display.text(stateName, PADDING + (WIDTH // 2) - 50, 40 + PADDING, scale=0.6)

    display.set_font("bitmap8")
    display.text("restart", PADDING + (WIDTH // 2) - 18, HEIGHT - 20)
    
def draw_stats_and_buttons(floor, health, healthMax, attack, defense):
    # Draw arrows and stats
    display.set_pen(0)
    display.set_font("bitmap6")
    
    display.text(f'Flr:{floor:2} Hp:{health:3}/{healthMax:3} Atk:{attack:2} Def:{defense:2}', PADDING, HEIGHT - 27)
    
    display.text("<", PADDING + 10, HEIGHT - 15)
    display.text("select", PADDING + (WIDTH // 2) - 22, HEIGHT - 15)
    display.text(">", PADDING + (WIDTH) - 28, HEIGHT - 15)
    
    display.text("^", WIDTH - PADDING - 8, PADDING + 10)
    display.text("V", WIDTH - PADDING - 8, HEIGHT - 35)
    
    display.set_pen(2)
    heightOffset = 30
    widthOffset = 12
    display.line(WIDTH - PADDING - widthOffset, 0, WIDTH - PADDING - widthOffset, HEIGHT - heightOffset)
    display.line(0, HEIGHT - heightOffset, WIDTH - PADDING - widthOffset, HEIGHT - heightOffset)
    
# ------------------------------
#        Combat
# ------------------------------

def get_monster_level(floor):
    # Nice to have, add multiple levels on a floor
    return random.randint(max(1, floor - 1), floor)

def calc_monster_attack(baseAttack, level):
    
    return baseAttack + int(level * MONSTER_ATTACK_LEVEL_MULTIPLIER)

def calc_monster_defense(baseDefense, level):
    
    return baseDefense + int(level * MONSTER_DEFENSE_LEVEL_MULTIPLIER)

def init_combat():
    state["state"] = "Combat"
    floor = state["floor"]
    level = get_monster_level(floor)
    state["monster"] = gen_monster(level)

    monsters = []
     
    # traverse whole directory
    for file in os.listdir(r'/dungeon1/monster/'):
        # check the extension of files
        if file.endswith('.txt') and file.startswith('example') == False:
            if DEBUG_INPUTS:
                print(file)
            monster = parse_monster_file(file, level)
            if monster["floors"][0] <= floor and monster["floors"][1] >= floor:
                monsters.append(monster)
    # TODO: Cache the monster list so since the list getting longer slows this down.
    monster = state["monster"]
    if state["floor"] == 1 or len(monsters) == 0:
        # always do the slime first
        monster = parse_monster_file("slime.txt", level) 
    else:
        monster = monsters[random.randint(0, len(monsters)-1)]
        
    state["monster"] = monster
        
def parse_monster_file(monsterFileName, level):
    
    monsterState = gen_monster(level)
    fileNamePart = monsterFileName.split(".")[0]
    
    filePath = f"/dungeon1/monster/{monsterFileName}"
    # Open the badge file
    try:
        monsterFile = open(filePath, "r")
    except OSError:
        print(f"could not load file {filePath}")
        return monsterState
        
    # Read in the lines
    try:
        monsterState["name"] = monsterFile.readline().strip()
        monsterState["fileName"] = fileNamePart
        monsterState["level"] = level
        monsterState["message"] = monsterFile.readline().strip()
        monsterState["attack"] = calc_monster_attack(int(monsterFile.readline()), level)
        monsterState["defense"] = calc_monster_defense(int(monsterFile.readline()), level)
        
        attackRatio = int(monsterFile.readline())
        blockRatio = int(monsterFile.readline())
        heavyAttackRatio = int(monsterFile.readline())
        monsterState["ratio"] = [attackRatio, blockRatio, heavyAttackRatio]
        
        minFloor = int(monsterFile.readline())
        maxFloor = int(monsterFile.readline())
        monsterState["floors"] = [minFloor, maxFloor]
        
    except Exception as error:
        monsterState = gen_monster(level)
        print("Monster load error:", error)
    
    return monsterState

def do_combat():
    attack = state["attack"]
    defense = state["defense"]
    health = state["health"]
    selectAction = state["combat"]["select"] # Attack, Block, Heavy, Potion
    monster = state["monster"]
    healing = state["healing"]
    attackMultiplier = state["combat"]["multiplier"] 
    
    monsterAttack = monster["attack"]
    monsterDefense = monster["defense"]

    monsterHealth = monster["health"]
    
    if monsterHealth < 1:
        
        end_combat()
        return
    
    monsterActionRatio = random.randint(0, 10)
    monsterAction = 0 # Attack, Block, Heavy
    
    # add ratios until we have the right number
    monsterActionCounter = 0
    for num in monster["ratio"]:
        monsterActionCounter += num
        if monsterActionRatio <= monsterActionCounter:
            break
        monsterAction += 1
        
    if DEBUG_INPUTS:
        print(f'ratio:{monsterActionRatio}, maction:{monsterAction}')
    if DEBUG_INPUTS == False:   
        monsterAction %= 3 # cap just in case
    
    damageMessage = ""
    fullMessage = "";
    
    if selectAction == 0 or selectAction == 2:
        damage = max(1, attack - monsterDefense) * attackMultiplier
        damage = calc_damage(damage, selectAction, monsterAction)
        damageMessage = f"It took {damage} dmg."

        monsterHealth -= damage
        attackMultiplier = 1
    elif selectAction == 1: # block
        damageMessage = f"You blocked and readied an attack."
        attackMultiplier += 1
    elif selectAction == 3:
        health = heal(health, healing, MAX_HEALTH)
        damageMessage = f"You healed {healing}."

    if monsterHealth < 1:
        fullMessage = f"took {damage} dmg and died. You won!"
    elif monsterAction == 0:
        monsterDamage = max(1, monsterAttack - defense)
        fullMessage = f"attacked ({monsterDamage}). {damageMessage}"
        health -= monsterDamage
        if selectAction == 1: # blocked, retaliate
            attackMultiplier += 1
    elif monsterAction == 1:
        fullMessage = f"blocked. {damageMessage}"
    elif monsterAction == 2:
        monsterDamage = max(1, monsterAttack - defense)
        fullMessage = f"heavy attacked ({monsterDamage}). {damageMessage}"
        health -= monsterDamage
    else:
        fullMessage = f"unknown action {monsterAction}. {damageMessage}"
    
    state["health"] = health;
    monster["health"] = monsterHealth;
    monster["message"] = fullMessage
    state["monster"] = monster;
    state["combat"]["multiplier"] = attackMultiplier

    if health < 1:
        # you dead
        state["state"] = "Dead"
        
def end_combat():
    newGold = state["monster"]["level"] * COMBAT_END_GOLD_MULTIPLIER
    state["gold"] += int(newGold)
    
    state["state"] = "Room"
    
    # Clear Room
    clear_current_room()
    
def heal(current, amount, maxHealth):
    health = min(maxHealth, current + amount)
    return health

        
def calc_damage(baseDamage, actionAttacker, actionDefender):
    damage = baseDamage
    if actionAttacker == 2: # heavy
        if actionDefender == 0: # defender is quicker
            damage //= 2
        if actionDefender == 1: # Guard break
            damage *= 2
    elif actionAttacker == 0: # attack
        if actionDefender == 2: # punish the heavy attack
            damage *= 2
        if actionDefender == 1: # blocked
            damage //= 2
    return damage
    
# ------------------------------
#        Map Rooms
# ------------------------------

def clear_current_room():
    location = state["location"]
    layout = state["layout"]
    currentRoom = layout[location]
    
    currentRoom["cleared"] = True
    layout[location] = currentRoom
    state["layout"] = layout
    

def map_room_move(direction):
        
    location = state["location"]
    layout = state["layout"]
    currentRoom = layout[location]
    
    if map_can_move() == False:
        print(f"Can't move in room {location}")
        return
    
    if direction == 'N' and currentRoom['n'] >= 0:
        location = currentRoom['n']
        state["location"] = location
        print(f"Moved to room {location}")
    elif direction == 'S' and currentRoom['s'] >= 0:
        location = currentRoom['s']
        state["location"] = location
        print(f"Moved to room {location}")
    elif direction == 'E' and currentRoom['e'] >= 0:
        location = currentRoom['e']
        state["location"] = location
        print(f"Moved to room {location}")
    elif direction == 'W' and currentRoom['w'] >= 0:
        location = currentRoom['w']
        state["location"] = location
        print(f"Moved to room {location}")

    # TODO, add all the directions
    
    currentRoom = layout[location]
    roomType = currentRoom["type"]
        
    if roomType == "E" or roomType == "S" or roomType == "N":
        currentRoom["cleared"] = True
        layout[location] = currentRoom
        state["layout"] = layout
    
def map_can_move():
    
    location = state["location"]
    layout = state["layout"]
    currentRoom = layout[location]
    
    if currentRoom["cleared"]:
        return True
    
    roomType = currentRoom["type"]
    
    # As long as room is not treasure and monster, auto clear it if it is not already.
    if roomType == "E" or roomType == "S" or roomType == "N":
        currentRoom["cleared"] = True
        layout[location] = currentRoom
        state["layout"] = layout
        return True
    
    return False

def map_room_confirm():
    
    location = state["location"]
    layout = state["layout"]
    currentRoom = layout[location]
    
    roomType = currentRoom["type"]

    if roomType == "S":
        # Next floor
        move_to_next_floor()
        state["state"] = "Shop"
        return
    
    if currentRoom["cleared"] == True:
        return
    
    if roomType == "M":
        init_combat()
    elif roomType == "T":
        # Give treasure
        floor = state["floor"]
        state["gold"] += random.randint(4 + floor, 4 + (2 * floor))
        clear_current_room()
        
def move_to_next_floor():
    state["floor"] += 1
    healing = state["healing"]
    state["health"] = heal(state["health"], healing, MAX_HEALTH) # heal amout of health when going to next floor
    state["layout"] = gen_floor(state["floor"])
    state["location"] = 0
    
# ------------------------------
#        Shop
# ------------------------------

def shop_confirm():
    
    shopSelect = state["shop"]["select"]
    
    if shopSelect == 3:
        state["shop"]["select"] = 1 # Reset for next time
        state["state"] = "Room"
    else:
        shop_buy()

def shop_buy():
    
    shopSelect = state["shop"]["select"]
    
    gold = state["gold"]
    
    stateToChange = ""
    shopIndex = ""
    changeAmount = 1
    priceIncrease = 1
    purchaseMessage = ""
    if shopSelect == 0:
        # Buy weapon
        shopIndex = "weaponCost"
        stateToChange = "attack"
        changeAmount = SHOP_ATTACK_ADDITION
        priceIncrease = 2
        purchaseMessage = "You bought a better weapon!"
    elif shopSelect == 1:
        # Buy armor
        shopIndex = "armorCost"
        stateToChange = "defense"
        changeAmount = SHOP_DEFENSE_ADDITION
        priceIncrease = 3
        purchaseMessage = "You bought better armor!"
    elif shopSelect == 2:
        # Buy potion
        shopIndex = "potionCost"
        stateToChange = "healing"
        changeAmount = SHOP_HEALING_ADDITION
        priceIncrease = 2
        purchaseMessage = "You can now heal better!"
    else:
        state["shop"]["actionMessage"] = f"Unknown action {shopSelect}"
        return
    
    cost = state["shop"][shopIndex]
    if cost > gold:
        state["shop"]["actionMessage"] = f'You cannot afford it.'
        return
    
    state[stateToChange] += changeAmount
    state["gold"] -= cost
    state["shop"][shopIndex] += priceIncrease
    state["shop"]["actionMessage"] = purchaseMessage
    

# ------------------------------
#        Program setup
# ------------------------------

# Create a new Badger and set it to update NORMAL
badger2040.system_speed(badger2040.SYSTEM_NORMAL)
display = badger2040.Badger2040()
display.led(128)
display.set_update_speed(badger2040.UPDATE_NORMAL)
display.set_thickness(2)

jpeg = jpegdec.JPEG(display.display)

state = default_state()
badger_os.state_load("dungeon1", state)

changed = False


# ------------------------------
#       Main program
# ------------------------------

draw_dungeon(state["state"])

while True:
    # Sometimes a button press or hold will keep the system
    # powered *through* HALT, so latch the power back on.
    display.keepalive()
    display.set_update_speed(badger2040.UPDATE_MEDIUM)
    
    stateName = state["state"]
    
    if stateName == "Title":
        if display.pressed(badger2040.BUTTON_B):
            state = default_state() # Reset the game for start
            state["state"] = "Room"
            print("Title Start!")
            changed = True
    elif stateName == "Dead":
        if display.pressed(badger2040.BUTTON_B):
            state = default_state()
            changed = True
    elif stateName == "Shop":
        display.set_update_speed(badger2040.UPDATE_FAST)
        if display.pressed(badger2040.BUTTON_A):
            # Fast scroll to the beginning    
            state["shop"]["select"] = 0
            changed = True
        if display.pressed(badger2040.BUTTON_B):
            shop_confirm()
            changed = True
        if display.pressed(badger2040.BUTTON_C):
            # Fast scroll to the end    
            state["shop"]["select"] = 3
            changed = True
        if display.pressed(badger2040.BUTTON_UP):
            select = state["shop"]["select"]
            select -= 1
            if select < 0:
                select = 3
            state["shop"]["select"] = select
            changed = True
        if display.pressed(badger2040.BUTTON_DOWN):
            select = state["shop"]["select"]
            select += 1
            select %= 4
            state["shop"]["select"] = select
            changed = True
    elif stateName == "Room":
        display.set_update_speed(badger2040.UPDATE_FAST)
        if DEBUG_INPUTS and display.pressed(badger2040.BUTTON_A) and display.pressed(badger2040.BUTTON_B):
            state["layout"] = gen_floor(state["floor"])
            state["location"] = 0
            changed = True
        elif display.pressed(badger2040.BUTTON_A):
            map_room_move('W')
            changed = True
            
        elif display.pressed(badger2040.BUTTON_B):
            map_room_confirm()
            changed = True
            
        elif display.pressed(badger2040.BUTTON_C):
            map_room_move('E')
            changed = True
            
        elif display.pressed(badger2040.BUTTON_UP):
            map_room_move('N')
            changed = True
                
        elif display.pressed(badger2040.BUTTON_DOWN):
            map_room_move('S')
            changed = True

    elif stateName == "Combat":
        display.set_update_speed(badger2040.UPDATE_FAST)

        if DEBUG_INPUTS and display.pressed(badger2040.BUTTON_A):
            # DEBUG init combat
            init_combat()
            changed = True
        elif display.pressed(badger2040.BUTTON_A):
            # Fast scroll to the beginning
            state["shop"]["select"] = 0
            changed = True
        if display.pressed(badger2040.BUTTON_B):
            # do combat
            do_combat()
            changed = True
        if display.pressed(badger2040.BUTTON_C):
            # Fast scroll to the end
            state["combat"]["select"] = 3
            changed = True
        if display.pressed(badger2040.BUTTON_UP):
            select = state["combat"]["select"]
            select -= 1
            if select < 0:
                select = 3
            state["combat"]["select"] = select
            changed = True
        if display.pressed(badger2040.BUTTON_DOWN):
            select = state["combat"]["select"]
            select += 1
            select %= 4
            state["combat"]["select"] = select
            changed = True
    else:
        # Unknown state, allow restart
        if display.pressed(badger2040.BUTTON_B):
            state = default_state()
            changed = True

    if changed:
        badger_os.state_save("dungeon1", state)
        if stateName != state["state"]:
            print("State Change: " + state["state"])
        draw_dungeon(state["state"])
        changed = False

    time.sleep(0.01)
    #display.halt()

