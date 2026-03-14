/**
 * API service utility functions
 */

import { API_BASE_URL, ENDPOINTS } from './config.js';

class ApiService {
    constructor(baseUrl = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                // Try to get error detail from response body
                let errorDetail = `HTTP ${response.status}`;
                try {
                    const errorBody = await response.json();
                    if (errorBody.detail) {
                        errorDetail = errorBody.detail;
                    }
                } catch {
                    // If response body is not JSON, use status text
                    errorDetail = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorDetail);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Health check
    async checkHealth() {
        return this.request(ENDPOINTS.health);
    }

    // Stores
    async getAllStores() {
        return this.request(ENDPOINTS.stores);
    }

    async getStore(storeName) {
        return this.request(`${ENDPOINTS.stores}/${storeName}`);
    }

    // MercadoLibre
    async getMercadoLibreDashboard(storeName) {
        const params = new URLSearchParams({ store: storeName });
        return this.request(`${ENDPOINTS.mercadolibre.dashboard}?${params}`);
    }

    async getMercadoLibreListings(filters = {}) {
        const params = new URLSearchParams();
        
        // Add non-null filters to params
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });

        return this.request(`${ENDPOINTS.mercadolibre.listings}?${params}`);
    }

    async getMercadoLibreStoreDashboard(storeName) {
        return this.request(ENDPOINTS.mercadolibre.storeDashboard(storeName));
    }

    async getMercadoLibreStoreListings(storeName, filters = {}) {
        const params = new URLSearchParams();

        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });

        const queryString = params.toString();
        const endpoint = ENDPOINTS.mercadolibre.storeListings(storeName);

        return this.request(queryString ? `${endpoint}?${queryString}` : endpoint);
    }

    async getListingMetrics(listingId) {
        return this.request(`/api/v1/listings/${listingId}/snapshots/metrics`);
    }

    // Orders
    async searchOrders(filters = {}) {
        const params = new URLSearchParams();

        // Add non-null filters to params
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });

        return this.request(`${ENDPOINTS.orders.search}?${params}`);
    }

    async getFilteredOrders(filters = {}) {
        const params = new URLSearchParams();

        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });

        return this.request(`${ENDPOINTS.orders.filter}?${params}`);
    }

    // Listings Bulk Actions
    async executeBulkAction(listing_ids, action_type, user_id = null, comment = null) {
        return this.request(ENDPOINTS.listings.bulkActions, {
            method: 'POST',
            body: JSON.stringify({
                listing_ids,
                action_type,
                user_id,
                comment
            })
        });
    }

    // Listings Actions History
    async getActionsHistory(filters = {}) {
        const params = new URLSearchParams();

        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });

        return this.request(`${ENDPOINTS.listings.actionsHistory}?${params}`);
    }

    async getBatchOperations(page = 1, page_size = 20) {
        const params = new URLSearchParams({ page: page.toString(), page_size: page_size.toString() });
        return this.request(`${ENDPOINTS.listings.actionsBatches}?${params}`);
    }

    async getActionsStatistics(days = 30) {
        const params = new URLSearchParams({ days: days.toString() });
        return this.request(`${ENDPOINTS.listings.actionsStats}?${params}`);
    }

    async getListingActionHistory(listing_id) {
        return this.request(ENDPOINTS.listings.listingHistory(listing_id));
    }

    // Update Listing
    async updateListing(listing_id, updateData) {
        return this.request(`/api/v1/listings/${listing_id}`, {
            method: 'PUT',
            body: JSON.stringify(updateData)
        });
    }

    // Relist Listing
    async relistListing(listing_id, relistData) {
        return this.request(`/api/v1/listings/${listing_id}/relist`, {
            method: 'POST',
            body: JSON.stringify(relistData)
        });
    }

    // Simple Visits Filter
    async filterListingsByVisits(listing_ids, max_visits, date_from, date_to, page = 1, limit = 50) {
        return this.request('/api/v1/visits/simple-filter/by-visits', {
            method: 'POST',
            body: JSON.stringify({
                listing_ids,
                max_visits,
                date_from,
                date_to,
                page,
                limit
            })
        });
    }

    async exportVisitsFilteredCSV(listing_ids, max_visits, date_from, date_to) {
        return this.request('/api/v1/visits/simple-filter/export-csv', {
            method: 'POST',
            body: JSON.stringify({
                listing_ids,
                max_visits,
                date_from,
                date_to
            })
        });
    }

    // Low-Traffic Listings
    async getLowTrafficListings(filters = {}) {
        const params = new URLSearchParams();

        // Add non-null filters to params
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });

        return this.request(`/api/v1/listings/low-traffic?${params}`);
    }

    async getAllLowTrafficIds(filters = {}) {
        const params = new URLSearchParams();

        // Add non-null filters to params
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });

        return this.request(`/api/v1/listings/low-traffic/ids-only?${params}`);
    }

    async exportLowTrafficCSV(listing_ids) {
        const response = await fetch(`${this.baseUrl}/api/v1/listings/low-traffic/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ listing_ids })
        });

        if (!response.ok) {
            throw new Error(`Failed to export CSV: ${response.statusText}`);
        }

        return await response.text();
    }

}

// Export a singleton instance
export const api = new ApiService();
export default api;
