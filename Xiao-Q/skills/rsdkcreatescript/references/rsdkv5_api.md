# RSDKv5 API Reference

Complete API reference for RSDKv5 (Sonic Mania engine).

## Object Lifecycle Functions

### Create()
Called when object is first created/spawned.

```c
Create:
    // Initialize object properties
    self.active = true
    self.visible = true
    self.position.x = 0
    self.position.y = 0
    self.velocity.x = 0
    self.velocity.y = 0
    return
```

### Update()
Called every frame while object is active.

```c
Update:
    // Per-frame logic
    self.position.x += self.velocity.x
    self.position.y += self.velocity.y
    return
```

### Draw()
Called every frame for rendering.

```c
Draw:
    // Render object
    DrawSprite(self.spriteIndex, self.animIndex, self.position.x, self.position.y, self.direction, 0)
    return
```

### StageLoad()
Called when stage is loaded (for static objects).

```c
StageLoad:
    // One-time setup for stage objects
    return
```

## Built-in Functions

### Player Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `GetPlayer()` | Get player object | object |
| `GetPlayer(n)` | Get player n (0-3) | object |
| `PlayerCheckCollisionBox(object, hitboxIndex)` | Check collision with player | bool |
| `PlayerCheckPushing(object)` | Check if player is pushing | bool |

### Collision Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `CheckCollisionBox(object, hitboxIndex)` | Check object collision | bool |
| `CheckCollisionPlatform(object, hitboxIndex)` | Check platform collision | bool |
| `CheckObjectCollision(int type, int group)` | Check collision with object type | object |
| `CheckOnScreen(object)` | Check if object is on screen | bool |

### Sprite and Animation Functions

| Function | Description |
|----------|-------------|
| `DrawSprite(sprite, anim, x, y, direction, priority)` | Draw sprite frame |
| `SetAnimation(animIndex)` | Set current animation |
| `Animate()` | Advance animation frame |
| `GetAnimationFrame()` | Get current frame index |
| `ResetAnimation()` | Reset to first frame |

### Movement Functions

| Function | Description |
|----------|-------------|
| `MoveSinWave(amplitude, frequency)` | Move in sine wave |
| `MovePoint(x, y, speed)` | Move toward point |
| `TurnAround()` | Reverse direction |

### Audio Functions

| Function | Description |
|----------|-------------|
| `PlaySfx(sfxIndex)` | Play sound effect |
| `StopSfx(sfxIndex)` | Stop sound effect |
| `PlayMusic(musicIndex)` | Play music track |

### Math Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `abs(value)` | Absolute value | int/float |
| `sin(angle)` | Sine (angle in degrees) | float |
| `cos(angle)` | Cosine | float |
| `sqrt(value)` | Square root | float |
| `random(min, max)` | Random number in range | int |

### Object Management

| Function | Description | Returns |
|----------|-------------|---------|
| `CreateObject(type, x, y)` | Create new object | object |
| `DestroyObject(object)` | Destroy object | void |
| `FindObject(type)` | Find first object of type | object |
| `FindObjects(type)` | Find all objects of type | array |

## Object Properties

### Position and Movement

| Property | Type | Description |
|----------|------|-------------|
| `position.x` | int | X position |
| `position.y` | int | Y position |
| `velocity.x` | int | X velocity |
| `velocity.y` | int | Y velocity |
| `direction` | int | Facing direction (0=left, 1=right) |
| `gravity` | int | Gravity multiplier |
| `onGround` | bool | Is on ground |

### State and Control

| Property | Type | Description |
|----------|------|-------------|
| `active` | bool | Update enabled |
| `visible` | bool | Drawing enabled |
| `drawOrder` | int | Draw priority (higher = later) |
| `type` | int | Object type ID |
| `subType` | int | Object subtype |

### Collision

| Property | Type | Description |
|----------|------|-------------|
| `collision.top` | bool | Top collision |
| `collision.bottom` | bool | Bottom collision |
| `collision.left` | bool | Left collision |
| `collision.right` | bool | Right collision |

### Animation

| Property | Type | Description |
|----------|------|-------------|
| `spriteIndex` | int | Current sprite set |
| `animIndex` | int | Current animation |
| `frameIndex` | int | Current frame |
| `animSpeed` | int | Animation speed |

## Hitbox Structure

```c
// Define hitbox for collision
object.hitbox[0].left = -8
object.hitbox[0].top = -8
object.hitbox[0].right = 8
object.hitbox[0].bottom = 8
```

## Common Patterns

### Basic Enemy AI

```c
Create:
    self.velocity.x = -2
    return

Update:
    // Turn at edges
    if !self.onGround
        self.velocity.x = -self.velocity.x
    endif
    
    // Check player collision
    if PlayerCheckCollisionBox(self, 0)
        // Damage player
    endif
    return
```

### Collectible Item

```c
Create:
    self.collected = false
    self.animIndex = ANIM_SPARKLE
    return

Update:
    if !self.collected
        if PlayerCheckCollisionBox(self, 0)
            self.collected = true
            PlaySfx(SFX_COLLECT)
            DestroyObject(self)
        endif
    endif
    return
```

### Moving Platform

```c
Create:
    self.startX = self.position.x
    self.startY = self.position.y
    self.moveSpeed = 2
    self.moveDistance = 64
    self.movingForward = true
    return

Update:
    if self.movingForward
        self.position.x += self.moveSpeed
        if self.position.x > self.startX + self.moveDistance
            self.movingForward = false
        endif
    else
        self.position.x -= self.moveSpeed
        if self.position.x < self.startX
            self.movingForward = true
        endif
    endif
    return
```
