from gym.envs.registration import register
from gym_aigame.envs.ai_game_env import *

class EmptyEnv(AIGameEnv):
    """
    Empty grid environment, no obstacles, sparse reward
    """

    def __init__(self, size=8):
        super(EmptyEnv, self).__init__(gridSize=size, maxSteps=2 * size)

class EmptyEnv6x6(EmptyEnv):
    def __init__(self):
        super(EmptyEnv6x6, self).__init__(size=6)

register(
    id='AIGame-Empty-8x8-v0',
    entry_point='gym_aigame.envs:EmptyEnv',
    reward_threshold=1000.0
)

register(
    id='AIGame-Empty-6x6-v0',
    entry_point='gym_aigame.envs:EmptyEnv6x6',
    reward_threshold=1000.0
)

class DoorKeyEnv(AIGameEnv):
    """
    Environment with a door and key, sparse reward
    """

    def __init__(self, size=8):
        super(DoorKeyEnv, self).__init__(gridSize=size, maxSteps=4 * size)

    def _genGrid(self, width, height):
        grid = super(DoorKeyEnv, self)._genGrid(width, height)
        assert width == height
        gridSz = width

        # Create a vertical splitting wall
        splitIdx = self.np_random.randint(2, gridSz-3)
        for i in range(0, gridSz):
            grid.set(splitIdx, i, Wall())

        # Place a door in the wall
        doorIdx = self.np_random.randint(1, gridSz-2)
        grid.set(splitIdx, doorIdx, Door('yellow'))
        self.doorPos=(splitIdx,doorIdx)

        # Place a key on the left side
        #keyIdx = self.np_random.randint(1 + gridSz // 2, gridSz-2)
        keyIdx = gridSz-2
        grid.set(1, keyIdx, Key('yellow'))
        self.keyPos=(1,keyIdx)
        return grid

class DoorKeyEnv16x16(DoorKeyEnv):
    def __init__(self):
        super(DoorKeyEnv16x16, self).__init__(size=16)

register(
    id='AIGame-Door-Key-8x8-v0',
    entry_point='gym_aigame.envs:DoorKeyEnv',
    reward_threshold=1000.0
)

register(
    id='AIGame-Door-Key-16x16-v0',
    entry_point='gym_aigame.envs:DoorKeyEnv16x16',
    reward_threshold=1000.0
)

class Room:
    def __init__(self,
        top,
        size,
        entryDoorPos,
        exitDoorPos,
        entryDoor,
        exitDoor
    ):
        self.top = top
        self.size = size
        self.entryDoorPos = entryDoorPos
        self.exitDoorPos = exitDoorPos
        self.exitDoor = exitDoor

class MultiRoomEnv(AIGameEnv):
    """
    Environment with multiple rooms (subgoals)
    """

    def __init__(self, numRooms):
        assert numRooms > 0
        self.numRooms = numRooms
        self.rooms = []

        super(MultiRoomEnv, self).__init__(gridSize=25, maxSteps=numRooms * 20)

    def _genGrid(self, width, height):

        roomList = []

        for i in range(0, 5):

            curRoomList = []

            entryDoorPos = (
                self.np_random.randint(0, width - 2),
                self.np_random.randint(0, width - 2)
            )

            # Recursively place the rooms
            self._placeRoom(
                self.numRooms,
                roomList=curRoomList,
                minSz=4,
                maxSz=10,
                entryDoorWall=2,
                entryDoorPos=entryDoorPos
            )

            if len(curRoomList) > len(roomList):
                roomList = curRoomList

            if len(roomList) == self.numRooms:
                break

        # Store the list of rooms in this environment
        assert len(roomList) > 0
        self.rooms = roomList

        # Randomize the starting agent position
        topX, topY = roomList[0].top
        sizeX, sizeY = roomList[0].size
        self.startPos = (
            self.np_random.randint(topX + 1, topX + sizeX - 2),
            self.np_random.randint(topY + 1, topY + sizeY - 2)
        )

        # Create the grid
        grid = Grid(width, height)
        wall = Wall()

        prevDoorColor = None

        # For each room
        for idx, room in enumerate(roomList):

            topX, topY = room.top
            sizeX, sizeY = room.size

            for i in range(0, sizeX):
            # Draw the top and bottom walls
                grid.set(topX + i, topY, wall)
                grid.set(topX + i, topY + sizeY - 1, wall)

            # Draw the left and right walls
            for j in range(0, sizeY):
                grid.set(topX, topY + j, wall)
                grid.set(topX + sizeX - 1, topY + j, wall)

            # If this isn't the first room, place the entry door
            if idx > 0:
                # Pick a door color different from the previous one
                doorColors = set( COLORS.keys() )
                if prevDoorColor:
                    doorColors.remove(prevDoorColor)
                doorColor = self.np_random.choice(tuple(doorColors))

                room.entryDoor = Door(doorColor)
                grid.set(*room.entryDoorPos, room.entryDoor)
                prevDoorColor = doorColor

                prevRoom = roomList[idx-1]
                prevRoom.exitDoorPos = room.entryDoorPos
                prevRoom.exitDoor = room.entryDoor

        # Place the final goal
        goalX = self.np_random.randint(topX + 1, topX + sizeX - 2)
        goalY = self.np_random.randint(topY + 1, topY + sizeY - 2)
        grid.set(goalX, goalY, Goal())
        self.goalPos=(goalX, goalY)
        return grid

    def _placeRoom(
        self,
        numLeft,
        roomList,
        minSz,
        maxSz,
        entryDoorWall,
        entryDoorPos
    ):
        # Choose the room size randomly
        sizeX = self.np_random.randint(minSz, maxSz)
        sizeY = self.np_random.randint(minSz, maxSz)
        #print('sizeX = %d, sizeY = %d' % (sizeX, sizeY))

        # The first room will be at the door position
        if len(roomList) == 0:
            topX, topY = entryDoorPos
        # Entry on the right
        elif entryDoorWall == 0:
            topX = entryDoorPos[0] - sizeX + 1
            y = entryDoorPos[1]
            topY = self.np_random.randint(y - sizeY + 2, y)
        # Entry wall on the south
        elif entryDoorWall == 1:
            x = entryDoorPos[0]
            topX = self.np_random.randint(x - sizeX + 2, x)
            topY = entryDoorPos[1] - sizeY + 1
        # Entry wall on the left
        elif entryDoorWall == 2:
            topX = entryDoorPos[0]
            y = entryDoorPos[1]
            topY = self.np_random.randint(y - sizeY + 2, y)
        # Entry wall on the top
        elif entryDoorWall == 3:
            x = entryDoorPos[0]
            topX = self.np_random.randint(x - sizeX + 2, x)
            topY = entryDoorPos[1]
        else:
            assert False, entryDoorWall

        #print('entryDoorWall=%d' % entryDoorWall)
        #print('doorX=%s, doorY=%s' % entryDoorPos)
        #print('topX = %d, topY = %d' % (topX, topY))

        # If the room is out of the grid, can't place a room here
        if topX < 0 or topY < 0:
            return False
        if topX + sizeX > self.gridSize or topY + sizeY >= self.gridSize:
            return False

        # If the room intersects with previous rooms, can't place it here
        for room in roomList[:-1]:
            nonOverlap = \
                topX + sizeX < room.top[0] or \
                room.top[0] + room.size[0] <= topX or \
                topY + sizeY < room.top[1] or \
                room.top[1] + room.size[1] <= topY

            if not nonOverlap:
                return False

        # Add this room to the list
        roomList.append(Room(
            (topX, topY),
            (sizeX, sizeY),
            entryDoorPos,
            None,
            None,
            None
        ))

        # If this was the last room, stop
        if numLeft == 1:
            return True

        # Try placing the next room
        for i in range(0, 8):

            # Pick which wall to place the out door on
            wallSet = set((0, 1, 2, 3))
            wallSet.remove(entryDoorWall)
            exitDoorWall = self.np_random.choice(tuple(wallSet))
            nextEntryWall = (exitDoorWall + 2) % 4

            # Pick the exit door position
            # Exit on right wall
            if exitDoorWall == 0:
                exitDoorPos = (
                    topX + sizeX - 1,
                    topY + self.np_random.randint(1, sizeY - 1)
                )
            # Exit on south wall
            elif exitDoorWall == 1:
                exitDoorPos = (
                    topX + self.np_random.randint(1, sizeX - 1),
                    topY + sizeY - 1
                )
            # Exit on left wall
            elif exitDoorWall == 2:
                exitDoorPos = (
                    topX,
                    topY + self.np_random.randint(1, sizeY - 1)
                )
            # Exit on north wall
            elif exitDoorWall == 3:
                exitDoorPos = (
                    topX + self.np_random.randint(1, sizeX - 1),
                    topY
                )
            else:
                assert False

            # Recursively create the other rooms
            success = self._placeRoom(
                numLeft - 1,
                roomList=roomList,
                minSz=minSz,
                maxSz=maxSz,
                entryDoorWall=nextEntryWall,
                entryDoorPos=exitDoorPos
            )

            if success:
                break

        return True

class MultiRoomEnvN6(MultiRoomEnv):
    def __init__(self):
        super(MultiRoomEnvN6, self).__init__(numRooms=6)

register(
    id='AIGame-Multi-Room-N6-v0',
    entry_point='gym_aigame.envs:MultiRoomEnvN6',
    reward_threshold=1000.0
)
