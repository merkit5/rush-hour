// src/services/levelService.js

import { easyLevels_5x5 } from '../levels/easy_5x5'
import { mediumLevels_5x5 } from '../levels/medium_5x5'
import { hardLevels_5x5 } from '../levels/hard_5x5'
import { easyLevels_6x6 } from '../levels/easy_6x6'
import { mediumLevels_6x6 } from '../levels/medium_6x6'
import { hardLevels_6x6 } from '../levels/hard_6x6'
import { easyLevels_7x7 } from '../levels/easy_7x7'
import { mediumLevels_7x7 } from '../levels/medium_7x7'
import { hardLevels_7x7 } from '../levels/hard_7x7'

export const getLevels = (size, difficulty) => {
  const levels = {
    '5x5': {
      easy: easyLevels_5x5,
      medium: mediumLevels_5x5,
      hard: hardLevels_5x5
    },
    '6x6': {
      easy: easyLevels_6x6,
      medium: mediumLevels_6x6,
      hard: hardLevels_6x6
    },
    '7x7': {
      easy: easyLevels_7x7,
      medium: mediumLevels_7x7,
      hard: hardLevels_7x7
    }
  }
  
  return levels[size]?.[difficulty] || levels['6x6'].easy
}

export const parseStringLevel = (levelStr, width, height, exitRow) => {
  const grid = Array(height).fill().map(() => Array(width + 1).fill(0))
  
  // Set exit position
  grid[exitRow][width] = 99
  
  const chars = levelStr.split('')
  let charIndex = 0
  
  for (let row = 0; row < height; row++) {
    for (let col = 0; col < width; col++) {
      if (charIndex >= chars.length) continue
      
      const char = chars[charIndex++]
      switch (char) {
        case 'o': grid[row][col] = 0; break
        case 'x': grid[row][col] = -1; break
        case 'A': grid[row][col] = 1; break
        default:
          if (char >= 'B' && char <= 'Z') {
            grid[row][col] = char.charCodeAt(0) - 64 + 1
          }
          break
      }
    }
  }
  
  return grid
}