"""
A simple, single-file platformer example featuring player movement, gravity,
and collision handling.

The physics algorithm is adapted from the following article:
https://maddythorson.medium.com/celeste-and-towerfall-physics-d24bd2ae0fc5
"""

import pyxel

# tweak these to your liking.
GRAVITY = 0.2
JUMP_POWER = 2

# width and height of game window.
W = 128
H = 128

# size of a single tile. in this example, tiles are square and match the size
# of the sprites in the editor.
TILE_SIZE = 8

# tile IDs. these map to the order of the tiles in the editor.
# these allow us to do things like check for collisions with walls, and find the
# player on the map when the game starts.
EMPTY_TILE = 0
PLAYER_TILE = 1
WALL_TILES = [2, 3, 4, 5]


def btni(key):
    """
    Returns 1 if the given key is pressed, 0 otherwise.
    This is useful for directional keys, as in the following example:
        move = btni(KEY_RIGHT) - btni(KEY_LEFT)
    `move` would be set to 1 if right is pressed, -1 if left is pressed, and 0
    if neither or both are pressed.
    """
    return int(pyxel.btn(key))


def check_collision(x, y):
    """
    Returns true if the given coordinates are inside a wall tile. This checks a
    bounding box the size of a single tile.
    """
    tilemap = pyxel.tilemap(0)

    # position in tilemap coordinates.
    # it's possible for the player to cover up to 4 tiles at the same time,
    # so we have to check in several places.
    tx0 = int(x // TILE_SIZE)
    ty0 = int(y // TILE_SIZE)
    tx1 = int((x + TILE_SIZE - 1) // TILE_SIZE)
    ty1 = int((y + TILE_SIZE - 1) // TILE_SIZE)

    # return true if any tile covered by the player is a wall.
    for y in range(ty0, ty1 + 1):
        for x in range(tx0, tx1 + 1):
            if tilemap.get(x, y) in WALL_TILES:
                return True

    # return false if no wall was found.
    return False


class Actor:
    def __init__(self, x, y):
        # position.
        self.x = x
        self.y = y

        # how much we still need to move by. used by move_x(...) and move_y(...)
        self.x_remainder = 0
        self.y_remainder = 0

    def move_x(self, amount, on_collision=None):
        """
        Moves the actor by the given amount in the X-axis, and calls the given
        `on_collision` callback if the actor hits a wall.
        """
        self.x_remainder += amount

        # how many whole pixels we can move.
        move = round(self.x_remainder)

        if move == 0:
            # we don't move by fractional amounts, so we save the remainder for
            # next time this method is called.
            return

        self.x_remainder -= move

        # sign is used to determine whether we're moving left (-1) or right (1).
        sign = 1 if move > 0 else -1

        # step one pixel at a time until we reach the end of the move, or until
        # we collide with something.
        while move != 0:
            # check if we can move in the desired direction.
            if check_collision(self.x + sign, self.y):
                # we hit something, so stop moving.
                if on_collision:
                    on_collision()
                return
            else:
                # move by one pixel.
                self.x += sign
                move -= sign

    def move_y(self, amount, on_collision=None):
        """
        Moves the actor by the given amount in the Y-axis, and calls the given
        `on_collision` callback if the actor hits a wall.
        """
        self.y_remainder += amount

        # how many whole pixels we can move.
        move = round(self.y_remainder)

        if move == 0:
            # we don't move by fractional amounts, so we save the remainder for
            # next time this method is called.
            return

        self.y_remainder -= move

        # sign is used to determine whether we're moving up (-1) or down (1).
        sign = 1 if move > 0 else -1

        # step one pixel at a time until we reach the end of the move, or until
        # we collide with something.
        while move != 0:
            # check if we can move in the desired direction.
            if check_collision(self.x, self.y + sign):
                # we hit something, so stop moving.
                if on_collision:
                    on_collision()
                return
            else:
                # move by one pixel.
                self.y += sign
                move -= sign


class Player(Actor):
    def __init__(self, x, y):
        super().__init__(x, y)

        # velocity to allow for more interesting non-linear movement.
        self.vx = 0
        self.vy = 0

    def update(self):
        """
        Updates the player's position and handles player input.
        """
        self.move_x(self.vx, on_collision=self.on_horizontal_collision)
        self.move_y(self.vy, on_collision=self.on_vertical_collision)

        # apply horizontal user input directly to X-axis velocity.
        self.vx = btni(pyxel.KEY_RIGHT) - btni(pyxel.KEY_LEFT)

        self.apply_gravity()

        # allow the player to jump.
        if pyxel.btnp(pyxel.KEY_UP):
            self.jump()

    def apply_gravity(self):
        """
        Applies gravity to the player.
        This could be as simple as the following:
            self.vy += GRAVITY

        However, this does not make for a satisfying jump. Instead, we apply
        different amounts of gravity depending on what the user is doing.

        If we're moving upwards, gravity is reduced.
        If the user continues holding the jump button, gravity is reduced more.

        This allows for a more controllable & better-feeling jump.
        """
        gravity_to_apply = GRAVITY

        if self.vy < 0:
            gravity_to_apply *= 0.7

            if pyxel.btn(pyxel.KEY_UP):
                gravity_to_apply *= 0.6

        self.vy += gravity_to_apply

    def jump(self):
        """
        Makes the player jump if they are on the ground.
        """
        if check_collision(self.x, self.y + TILE_SIZE):
            self.vy = -JUMP_POWER

    def on_horizontal_collision(self):
        """
        Called when the player hits a wall while moving horizontally.
        """
        self.vx = 0

    def on_vertical_collision(self):
        """
        Called when the player hits a wall while moving vertically.
        """
        self.vy = 0


class Game:
    def __init__(self) -> None:
        pyxel.init(W, H, caption="Platformer Example", fps=60)
        pyxel.load("assets.pyxres")

        self.player = Player(W / 2, H / 2)

        self.scan_map()

    def scan_map(self):
        """
        Finds the player on the map.
        This function can also be used to find enemies, items, et cetera.
        I have intentionally left this loop without a break so that new objects
        can be added easily.
        """
        tilemap = pyxel.tilemap(0)
        for y in range(tilemap.height):
            for x in range(tilemap.width):
                tile = tilemap.get(x, y)
                if tile == PLAYER_TILE:
                    self.player.x = x * TILE_SIZE
                    self.player.y = y * TILE_SIZE
                    tilemap.set(x, y, EMPTY_TILE)

    def run(self):
        """
        Starts the game running.
        """
        pyxel.run(self.update, self.draw)

    def update(self):
        self.player.update()

    def draw(self):
        # draw map
        pyxel.bltm(0, 0, 0, 0, 0, W, H)

        # draw player
        pyxel.blt(
            self.player.x,
            self.player.y,
            0,
            PLAYER_TILE * TILE_SIZE,
            0,
            TILE_SIZE,
            TILE_SIZE,
            0,
        )


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
