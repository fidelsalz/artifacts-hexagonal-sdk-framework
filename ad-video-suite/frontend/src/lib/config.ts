export const API_BASE =
	import.meta.env.VITE_API_BASE_URL ??
	(typeof window !== 'undefined'
		? `${window.location.protocol}//${window.location.hostname}:8011`
		: 'http://localhost:8011');
