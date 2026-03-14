/**
 * Theme system exports and utilities
 */

import type { ThemePresets, PresetTheme, StyleConfig, ThemeType } from '../types/themes.js'
import { lightTheme } from './light.js'
import { darkTheme } from './dark.js'

// Available theme presets
export const themePresets: ThemePresets = {
  light: lightTheme,
  dark: darkTheme,
  auto: {
    name: 'auto',
    displayName: 'Auto Theme',
    description: 'Automatically switches between light and dark based on system preference',
    config: lightTheme.config // Default to light, will be overridden by auto detection
  },
  highContrast: {
    name: 'highContrast',
    displayName: 'High Contrast',
    description: 'High contrast theme for accessibility',
    config: {
      ...lightTheme.config,
      colors: {
        ...lightTheme.config.colors,
        primary: '#000000',
        background: '#ffffff',
        text: '#000000',
        border: '#000000'
      }
    }
  },
  minimal: {
    name: 'minimal',
    displayName: 'Minimal',
    description: 'Clean minimal theme with reduced visual elements',
    config: {
      ...lightTheme.config,
      borderRadius: 'none',
      colors: {
        ...lightTheme.config.colors,
        border: 'transparent',
        hover: '#f8fafc'
      },
      table: {
        ...lightTheme.config.table,
        stripedRows: false,
        borderStyle: 'none'
      },
      cards: {
        ...lightTheme.config.cards,
        shadow: 'none',
        border: false
      }
    }
  },
  colorful: {
    name: 'colorful',
    displayName: 'Colorful',
    description: 'Vibrant theme with rich colors',
    config: {
      ...lightTheme.config,
      colors: {
        ...lightTheme.config.colors,
        primary: '#8b5cf6',
        secondary: '#ec4899',
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        info: '#06b6d4',
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }
    }
  }
}

// Theme utilities
export function getTheme(themeName: ThemeType): PresetTheme {
  return themePresets[themeName] || themePresets.light
}

export function getAutoTheme(): PresetTheme {
  if (typeof window !== 'undefined' && window.matchMedia) {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    return isDark ? themePresets.dark : themePresets.light
  }
  return themePresets.light
}

export function mergeThemeConfig(base: StyleConfig, override: Partial<StyleConfig>): StyleConfig {
  return {
    ...base,
    ...override,
    colors: {
      ...base.colors,
      ...override.colors
    },
    table: {
      ...base.table,
      ...override.table
    },
    cards: {
      ...base.cards,
      ...override.cards
    },
    grid: {
      ...base.grid,
      ...override.grid
    },
    list: {
      ...base.list,
      ...override.list
    }
  }
}

export function applyThemeToElement(element: HTMLElement, config: StyleConfig): void {
  if (!element || !config.colors) return

  const colors = config.colors
  const style = element.style

  // Apply CSS custom properties
  if (colors.primary) style.setProperty('--theme-primary', colors.primary)
  if (colors.secondary) style.setProperty('--theme-secondary', colors.secondary)
  if (colors.background) style.setProperty('--theme-background', colors.background)
  if (colors.surface) style.setProperty('--theme-surface', colors.surface)
  if (colors.text) style.setProperty('--theme-text', colors.text)
  if (colors.textSecondary) style.setProperty('--theme-text-secondary', colors.textSecondary)
  if (colors.border) style.setProperty('--theme-border', colors.border)
  if (colors.hover) style.setProperty('--theme-hover', colors.hover)
  if (colors.selected) style.setProperty('--theme-selected', colors.selected)

  // Apply status colors
  if (colors.success) style.setProperty('--theme-success', colors.success)
  if (colors.warning) style.setProperty('--theme-warning', colors.warning)
  if (colors.error) style.setProperty('--theme-error', colors.error)
  if (colors.info) style.setProperty('--theme-info', colors.info)

  // Apply border radius
  if (config.borderRadius) {
    const radiusMap = {
      none: '0',
      small: '0.25rem',
      medium: '0.5rem',
      large: '1rem'
    }
    style.setProperty('--theme-border-radius', radiusMap[config.borderRadius])
  }

  // Apply font size
  if (config.fontSize) {
    const fontSizeMap = {
      small: '0.875rem',
      medium: '1rem',
      large: '1.125rem'
    }
    style.setProperty('--theme-font-size', fontSizeMap[config.fontSize])
  }

  // Apply font family
  if (config.fontFamily) {
    style.setProperty('--theme-font-family', config.fontFamily)
  }
}

// Export theme presets individually
export { lightTheme, darkTheme }