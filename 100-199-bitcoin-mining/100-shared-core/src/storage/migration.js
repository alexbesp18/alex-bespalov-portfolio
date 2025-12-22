/**
 * Storage Migration Utilities
 * 
 * Utilities for migrating localStorage data between versions.
 * 
 * @module storage/migration
 */

import { createStorageManager } from './localStorage.js';

/**
 * @typedef {Object} Migration
 * @property {number} version - Target version number
 * @property {string} description - Description of the migration
 * @property {Function} migrate - Migration function (data) => newData
 */

/**
 * Create a migration manager for versioned storage
 * 
 * @param {string} namespace - Storage namespace
 * @param {number} currentVersion - Current app version
 * @returns {Object} Migration manager
 */
export const createMigrationManager = (namespace, currentVersion) => {
  const storage = createStorageManager(namespace);
  const versionKey = '_version';
  const migrations = [];
  
  return {
    /**
     * Register a migration
     * 
     * @param {number} version - Version this migration upgrades TO
     * @param {string} description - Migration description
     * @param {Function} migrate - Migration function
     */
    register: (version, description, migrate) => {
      migrations.push({ version, description, migrate });
      migrations.sort((a, b) => a.version - b.version);
    },
    
    /**
     * Get the current stored version
     * 
     * @returns {number} Current stored version (0 if not set)
     */
    getVersion: () => {
      return storage.get(versionKey, 0);
    },
    
    /**
     * Check if migrations are needed
     * 
     * @returns {boolean} Whether migrations need to run
     */
    needsMigration: () => {
      const storedVersion = storage.get(versionKey, 0);
      return storedVersion < currentVersion;
    },
    
    /**
     * Run all pending migrations
     * 
     * @param {Object} data - Current data to migrate
     * @returns {Object} Migrated data
     */
    runMigrations: (data) => {
      const storedVersion = storage.get(versionKey, 0);
      let migratedData = { ...data };
      
      const pendingMigrations = migrations.filter(m => m.version > storedVersion);
      
      for (const migration of pendingMigrations) {
        try {
          console.log(`Running migration to v${migration.version}: ${migration.description}`);
          migratedData = migration.migrate(migratedData);
        } catch (error) {
          console.error(`Migration to v${migration.version} failed:`, error);
          throw error;
        }
      }
      
      storage.set(versionKey, currentVersion);
      return migratedData;
    },
    
    /**
     * Set the current version
     * 
     * @param {number} version - Version to set
     */
    setVersion: (version) => {
      storage.set(versionKey, version);
    },
    
    /**
     * Get list of pending migrations
     * 
     * @returns {Migration[]} Pending migrations
     */
    getPendingMigrations: () => {
      const storedVersion = storage.get(versionKey, 0);
      return migrations.filter(m => m.version > storedVersion);
    },
  };
};

/**
 * Migrate data structure with defaults
 * Ensures all required fields exist with default values
 * 
 * @param {Object} data - Existing data
 * @param {Object} defaults - Default values
 * @param {Object} [options={}] - Migration options
 * @param {boolean} [options.removeUnknown=false] - Remove keys not in defaults
 * @returns {Object} Migrated data
 */
export const migrateWithDefaults = (data, defaults, options = {}) => {
  const { removeUnknown = false } = options;
  
  if (!data) return { ...defaults };
  
  const result = {};
  
  // Add all default keys
  for (const [key, defaultValue] of Object.entries(defaults)) {
    if (key in data) {
      // Handle nested objects
      if (defaultValue && typeof defaultValue === 'object' && !Array.isArray(defaultValue)) {
        result[key] = migrateWithDefaults(data[key], defaultValue, options);
      } else {
        result[key] = data[key];
      }
    } else {
      result[key] = defaultValue;
    }
  }
  
  // Optionally keep unknown keys
  if (!removeUnknown) {
    for (const [key, value] of Object.entries(data)) {
      if (!(key in result)) {
        result[key] = value;
      }
    }
  }
  
  return result;
};

/**
 * Rename keys in a data object
 * 
 * @param {Object} data - Data object
 * @param {Object} keyMap - Map of oldKey -> newKey
 * @returns {Object} Data with renamed keys
 */
export const renameKeys = (data, keyMap) => {
  const result = { ...data };
  
  for (const [oldKey, newKey] of Object.entries(keyMap)) {
    if (oldKey in result) {
      result[newKey] = result[oldKey];
      delete result[oldKey];
    }
  }
  
  return result;
};

/**
 * Convert array items with a transformer
 * 
 * @param {Array} array - Array to convert
 * @param {Function} transformer - Transform function for each item
 * @returns {Array} Transformed array
 */
export const migrateArrayItems = (array, transformer) => {
  if (!Array.isArray(array)) return array;
  return array.map(transformer);
};

/**
 * Merge storage from old keys to new structure
 * 
 * @param {Object} oldKeys - Map of category -> oldKey
 * @param {string} newKey - New combined key
 * @param {Object} defaults - Default values for new structure
 * @returns {Object} Merged data
 */
export const mergeStorageKeys = (oldKeys, newKey, defaults) => {
  const storage = createStorageManager('');
  const result = { ...defaults };
  
  for (const [category, oldKey] of Object.entries(oldKeys)) {
    const oldData = storage.get(oldKey);
    if (oldData !== null) {
      result[category] = oldData;
      storage.remove(oldKey);
    }
  }
  
  storage.set(newKey, result);
  return result;
};

/**
 * Create a backup before migration
 * 
 * @param {string} namespace - Storage namespace
 * @returns {string} Backup key
 */
export const createBackup = (namespace) => {
  const storage = createStorageManager(namespace);
  const backupKey = `_backup_${Date.now()}`;
  const allData = storage.getAll();
  storage.set(backupKey, allData);
  return backupKey;
};

/**
 * Restore from a backup
 * 
 * @param {string} namespace - Storage namespace
 * @param {string} backupKey - Backup key to restore
 * @returns {boolean} Whether restore succeeded
 */
export const restoreBackup = (namespace, backupKey) => {
  const storage = createStorageManager(namespace);
  const backup = storage.get(backupKey);
  
  if (!backup) return false;
  
  storage.clear();
  
  for (const [key, value] of Object.entries(backup)) {
    storage.set(key, value);
  }
  
  return true;
};

