/**
 * Frontend configuration
 */

// In development, use relative URLs to leverage Vite's proxy
// In production, use the environment variable or default to current origin
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8010';

export const ENDPOINTS = {
    health: '/health',
    stores: '/api/v1/stores/',
    runTask: '/run-task',
    mercadolibre: {
        listings: '/api/v1/mercadolibre/listings',
        dashboard: '/api/v1/mercadolibre/analytics/dashboard',
        storeListings: (storeName) => `/api/v1/mercadolibre/stores/${storeName}/listings`,
        storeDashboard: (storeName) => `/api/v1/mercadolibre/stores/${storeName}/analytics/dashboard`
    },
    orders: {
        search: '/api/v1/maintenance/orders/data/search',
        filter: '/api/v1/maintenance/orders/data/filter'
    },
    listings: {
        bulkActions: '/api/v1/listings/bulk-actions/execute',
        actionsHistory: '/api/v1/listings/actions/history',
        actionsBatches: '/api/v1/listings/actions/history/batches',
        actionsStats: '/api/v1/listings/actions/history/stats',
        listingHistory: (listing_id) => `/api/v1/listings/actions/history/listing/${listing_id}`
    }
};