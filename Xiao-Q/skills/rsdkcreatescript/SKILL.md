---
name: rsdk-script-dev
description: RSDK（Retro Engine Software Development Kit）脚本开发技能。支持 RSDKv3/v4/v5 多版本游戏模组开发，包括游戏对象(Object)创建、场景关卡设计、完整模组开发、代码模板生成等。触发词：RSDK、Retro Engine、Sonic Mania模组、游戏对象脚本、Object脚本、RSDKv5、RSDK脚本、创建对象、场景设计、rsdk script、retro engine mod。当用户需要开发 RSDK 脚本、创建游戏模组、编写对象逻辑、设计关卡时触发此技能。
---

# RSDK Script Development Skill

## Overview

This skill provides comprehensive guidance for developing RSDK (Retro Engine Software Development Kit) scripts and mods. It covers RSDKv3, RSDKv4, and RSDKv5 (used in Sonic Mania), supporting the full mod development workflow from object scripting to scene design and complete mod packaging.

## Core Capabilities

### 1. RSDK Version Detection and Setup

To determine the target RSDK version, check:
- User explicitly specifies version (RSDKv3/v4/v5)
- Project context indicates target game (Sonic Mania = RSDKv5, Sonic 1/2 Remastered = RSDKv4/v3)
- Default to RSDKv5 if unspecified (most common)

RSDK version differences:
- **RSDKv3**: Used in Sonic 1 Remastered, object scripts in C-like language
- **RSDKv4**: Used in Sonic 2 Remastered, enhanced object system
- **RSDKv5**: Used in Sonic Mania, most feature-rich, supports complex mods

### 2. Game Object (Object) Script Creation

To create an RSDK object script, follow this workflow:

1. **Define object properties**: Determine object type, subtype, and attributes
2. **Write object script**: Create `.txt` script file with proper RSDK syntax
3. **Implement lifecycle functions**: `Create`, `Update`, `Draw`, `StageLoad`
4. **Add collision and interaction logic**: Touch responses, player interaction
5. **Test and validate**: Check syntax and game behavior

Object script template structure:
```
// Object: [ObjectName]
// Type: [TypeID]

Create:
    // Initialization code
    return

Update:
    // Per-frame update logic
    return

Draw:
    // Rendering code
    return

StageLoad:
    // Called when stage loads
    return
```

### 3. Scene and Level Design

To design RSDK scenes and levels:

1. **Scene data structure**: Understand scene format for target RSDK version
2. **Entity placement**: Place objects, set positions and properties
3. **Trigger setup**: Configure triggers, checkpoints, boundaries
4. **Layer management**: Background/foreground layers, scrolling
5. **Collision and boundaries**: Set up collision paths and stage boundaries

### 4. Code Templates and Snippets

The skill provides reusable code templates stored in `assets/templates/`:

- **Basic Object Template**: Minimal object with Create/Update/Draw
- **Moving Platform Template**: Platform with movement patterns
- **Enemy Template**: Basic enemy with AI behavior
- **Collectible Template**: Ring/monitor/item collection logic
- **Player Interaction Template**: Objects that respond to player contact
- **Animation Template**: Sprite animation control
- **Sound Effect Template**: SFX playback integration

### 5. Complete Mod Development

To develop a complete RSDK mod:

1. **Project structure setup**: Create proper mod directory structure
2. **Object scripting**: Develop all custom objects needed
3. **Scene modification**: Edit or create scene data
4. **Asset integration**: Sprites, sounds, backgrounds
5. **Mod metadata**: Create `mod.ini` or equivalent config
6. **Testing and debugging**: Validate mod functionality
7. **Packaging**: Prepare mod for distribution

## RSDK Scripting Reference

### Basic Syntax (RSDKv5)

RSDK scripting uses a C-like language with these key elements:

**Variables and Types**:
- `int`: Integer values
- `float`: Floating point values
- `object`: Object references
- `entity`: Entity references

**Built-in Functions**:
- `GetPlayer()`: Get player object
- `CheckCollisionBox()`: Collision detection
- `DrawSprite()`: Render sprites
- `PlaySfx()`: Play sound effects
- `SetAnimation()`: Set sprite animation state

**Object Properties**:
- `position.x`, `position.y`: Object position
- `velocity.x`, `velocity.y`: Movement velocity
- `direction`: Facing direction (0=left, 1=right)
- `visible`: Render toggle
- `active`: Update toggle

### Version-Specific Differences

**RSDKv5 enhancements**:
- Enhanced animation system with `animator` object
- Improved collision with `Collide()` function
- Background scrolling with `ScrollInfo` structure
- Mod loader support with `ModAPI` integration

## Workflow Guidance

### Creating a New Object Script

1. Determine object purpose and behavior
2. Read `references/rsdkv5_api.md` for relevant functions
3. Use template from `assets/templates/basic_object.txt`
4. Implement required lifecycle functions
5. Add object to mod's object list
6. Test in-game using mod loader

### Modifying Existing Objects

1. Locate original object script in game data
2. Create override in mod directory
3. Modify desired behavior while preserving core functionality
4. Test to ensure compatibility

### Scene Editing Workflow

1. Extract scene data using RSDK data extraction tools
2. Parse scene format (version-specific)
3. Modify entity placements or create new scene
4. Repack scene data
5. Test level in-game

## Resources

### references/

- `references/rsdkv5_api.md`: Complete RSDKv5 API reference
- `references/rsdkv3_api.md`: RSDKv3 API reference (if needed)
- `references/rsdkv4_api.md`: RSDKv4 API reference (if needed)
- `references/scene_formats.md`: Scene data format documentation
- `references/mod_structure.md`: Mod directory structure guide

### assets/templates/

- `assets/templates/basic_object.txt`: Basic object template
- `assets/templates/moving_platform.txt`: Moving platform template
- `assets/templates/enemy_basic.txt`: Basic enemy AI template
- `assets/templates/collectible.txt`: Collectible item template
- `assets/templates/player_interact.txt`: Player interaction template
- `assets/templates/mod_ini.txt`: mod.ini configuration template

### scripts/

- `scripts/validate_syntax.py`: Validate RSDK script syntax
- `scripts/generate_object.py`: Generate object script from parameters
- `scripts/package_mod.py`: Package mod for distribution

## Important Notes

- RSDK scripts are plain text files, typically with `.txt` extension
- Object type IDs must be unique within a mod
- Test mods using the RSDK mod loader for the target game
- Backup original game data before modding
- Respect copyright - do not distribute extracted game assets

---

**Trigger words recap**: RSDK, Retro Engine, Sonic Mania, 游戏模组, 对象脚本, Object script, RSDKv5, mod development, scene design, 关卡设计
