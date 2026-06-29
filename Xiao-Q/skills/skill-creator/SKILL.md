---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, update or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run claude-with-access-to-the-skill on them
- Help the user evaluate the results both qualitatively and quantitatively
  - While the runs happen in the background, draft some quantitative evals if there aren't any
  - Use the eval-viewer/generate_review.py script to show the user the results
- Rewrite the skill based on feedback
- Repeat until you're satisfied

## Creating a skill

### Capture Intent

1. What should this skill enable Claude to do?
2. When should this skill trigger?
3. What's the expected output format?
4. Should we set up test cases?

### Write the SKILL.md

- **name**: Skill identifier
- **description**: When to trigger, what it does. Make it a bit pushy to avoid undertriggering.
- **the rest of the skill**

### Skill Writing Guide

Keep SKILL.md under 500 lines. Use imperative form. Explain the why, not just the what.

## Running and evaluating test cases

1. Spawn subagent runs with and without the skill
2. Draft assertions while runs are in progress
3. Grade and aggregate results
4. Launch the eval viewer for human review
5. Read feedback and iterate

Good luck!
