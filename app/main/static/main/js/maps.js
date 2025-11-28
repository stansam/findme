/**
 * FindMe Maps - Interactive Missing Persons Map
 * Production-ready with robust error handling and user feedback
 */

(function() {
    'use strict';

    // ========================================
    // Configuration & State
    // ========================================
    
    const FINDME_CONFIG = {
        mapCenter: [-1.286389, 36.817223], // Nairobi, Kenya
        mapZoom: 12,
        maxZoom: 18,
        minZoom: 6,
        clusterRadius: 50,
        tileLayer: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        updateInterval: 30000, // 30 seconds
        toastDuration: 4000
    };

    const FINDME_STATE = {
        map: null,
        markers: [],
        markerClusterGroup: null,
        currentFilters: {
            status: 'missing',
            days: '30',
            search: '',
            showSightings: true,
            showMinorsOnly: false,
            showClusters: true
        },
        userLocation: null,
        isFullscreen: false,
        updateTimer: null
    };

    // ========================================
    // DOM Elements
    // ========================================
    
    const FINDME_ELEMENTS = {
        map: document.getElementById('findmeMainMap'),
        loading: document.getElementById('findmeMapLoading'),
        filtersPanel: document.getElementById('findmeFiltersPanel'),
        statsPanel: document.getElementById('findmeStatsPanel'),
        toggleFiltersBtn: document.getElementById('findmeToggleFiltersBtn'),
        toggleStatsBtn: document.getElementById('findmeToggleStatsBtn'),
        applyFiltersBtn: document.getElementById('findmeApplyFiltersBtn'),
        resetFiltersBtn: document.getElementById('findmeResetFiltersBtn'),
        statusFilter: document.getElementById('findmeStatusFilter'),
        daysFilter: document.getElementById('findmeDaysFilter'),
        searchInput: document.getElementById('findmeSearchInput'),
        searchClearBtn: document.getElementById('findmeSearchClearBtn'),
        showSightingsCheckbox: document.getElementById('findmeShowSightings'),
        showMinorsOnlyCheckbox: document.getElementById('findmeShowMinorsOnly'),
        showClustersCheckbox: document.getElementById('findmeShowClusters'),
        locateMeBtn: document.getElementById('findmeLocateMeBtn'),
        fullscreenBtn: document.getElementById('findmeFullscreenBtn'),
        refreshMapBtn: document.getElementById('findmeRefreshMapBtn'),
        resultsCounter: document.getElementById('findmeResultsCounter'),
        resultsCount: document.getElementById('findmeResultsCount'),
        personModal: document.getElementById('findmePersonModal'),
        personModalOverlay: document.getElementById('findmePersonModalOverlay'),
        personModalClose: document.getElementById('findmePersonModalClose'),
        personModalBody: document.getElementById('findmePersonModalBody'),
        toast: document.getElementById('findmeToast'),
        toastMessage: document.getElementById('findmeToastMessage'),
        toastClose: document.getElementById('findmeToastClose')
    };

    // ========================================
    // Initialization
    // ========================================
    
    function findmeInitializeMap() {
        try {
            // Initialize Leaflet map
            FINDME_STATE.map = L.map('findmeMainMap', {
                center: FINDME_CONFIG.mapCenter,
                zoom: FINDME_CONFIG.mapZoom,
                maxZoom: FINDME_CONFIG.maxZoom,
                minZoom: FINDME_CONFIG.minZoom,
                zoomControl: true
            });

            // Add tile layer
            L.tileLayer(FINDME_CONFIG.tileLayer, {
                attribution: FINDME_CONFIG.attribution,
                maxZoom: FINDME_CONFIG.maxZoom
            }).addTo(FINDME_STATE.map);

            // Initialize marker cluster group
            FINDME_STATE.markerClusterGroup = L.markerClusterGroup({
                maxClusterRadius: FINDME_CONFIG.clusterRadius,
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: true,
                zoomToBoundsOnClick: true,
                iconCreateFunction: function(cluster) {
                    const count = cluster.getChildCount();
                    let className = 'marker-cluster-';
                    
                    if (count < 10) className += 'small';
                    else if (count < 50) className += 'medium';
                    else className += 'large';
                    
                    return L.divIcon({
                        html: '<div><span>' + count + '</span></div>',
                        className: 'marker-cluster ' + className,
                        iconSize: L.point(40, 40)
                    });
                }
            });

            FINDME_STATE.map.addLayer(FINDME_STATE.markerClusterGroup);

            findmeShowToast('Map initialized successfully', 'success');
            console.log('FindMe Map initialized');
        } catch (error) {
            console.error('Map initialization error:', error);
            findmeShowToast('Failed to initialize map', 'error');
        }
    }

    // ========================================
    // Data Fetching
    // ========================================
    
    async function findmeFetchMapMarkers() {
        try {
            findmeShowLoading(true);

            const params = new URLSearchParams({
                status: FINDME_STATE.currentFilters.status,
                days: FINDME_STATE.currentFilters.days,
                q: FINDME_STATE.currentFilters.search,
                include_sightings: FINDME_STATE.currentFilters.showSightings
            });

            const response = await fetch(`/api/maps/markers?${params.toString()}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                findmeRenderMarkers(data.markers);
                findmeUpdateResultsCounter(data.total);
                findmeShowToast(`Loaded ${data.total} markers`, 'success');
            } else {
                throw new Error(data.error || 'Failed to fetch markers');
            }
        } catch (error) {
            console.error('Error fetching markers:', error);
            findmeShowToast('Failed to load map data. Please try again.', 'error');
        } finally {
            findmeShowLoading(false);
        }
    }

    async function findmeFetchStatistics() {
        try {
            const response = await fetch('/api/maps/statistics', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                findmeRenderStatistics(data.statistics);
            } else {
                throw new Error(data.error || 'Failed to fetch statistics');
            }
        } catch (error) {
            console.error('Error fetching statistics:', error);
            findmeShowToast('Failed to load statistics', 'warning');
        }
    }

    async function findmeFetchPersonDetails(personId) {
        try {
            findmeShowLoading(true);

            const response = await fetch(`/api/maps/person/${personId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                findmeShowPersonModal(data.person);
            } else {
                throw new Error(data.error || 'Failed to fetch person details');
            }
        } catch (error) {
            console.error('Error fetching person details:', error);
            findmeShowToast('Failed to load person details', 'error');
        } finally {
            findmeShowLoading(false);
        }
    }

    // ========================================
    // Marker Creation & Rendering
    // ========================================
    
    function findmeCreateMarker(markerData) {
        let markerColor, iconName, markerClass;

        if (markerData.type === 'missing_person') {
            if (markerData.is_minor) {
                markerColor = 'red';
                iconName = 'child';
                markerClass = 'findme-marker-minor';
            } else {
                switch (markerData.status) {
                    case 'found':
                        markerColor = 'green';
                        iconName = 'check';
                        markerClass = 'findme-marker-found';
                        break;
                    case 'investigating':
                        markerColor = 'orange';
                        iconName = 'search';
                        markerClass = 'findme-marker-investigating';
                        break;
                    default:
                        markerColor = 'red';
                        iconName = 'user';
                        markerClass = 'findme-marker-missing';
                }
            }
        } else if (markerData.type === 'sighting') {
            markerColor = 'blue';
            iconName = 'eye';
            markerClass = 'findme-marker-sighting';
        }

        const icon = L.AwesomeMarkers.icon({
            icon: iconName,
            prefix: 'fa',
            markerColor: markerColor,
            extraClasses: markerClass
        });

        const marker = L.marker([markerData.lat, markerData.lng], { icon: icon });

        // Create popup content
        const popupContent = findmeCreatePopupContent(markerData);
        marker.bindPopup(popupContent, {
            maxWidth: 300,
            className: 'findme-custom-popup'
        });

        // Add click handler for details
        marker.on('click', function() {
            if (markerData.type === 'missing_person') {
                setTimeout(() => {
                    const viewDetailsBtn = document.getElementById(`findme-view-details-${markerData.id}`);
                    if (viewDetailsBtn) {
                        viewDetailsBtn.addEventListener('click', function(e) {
                            e.preventDefault();
                            findmeFetchPersonDetails(markerData.id);
                        });
                    }
                }, 100);
            }
        });

        return marker;
    }

    function findmeCreatePopupContent(data) {
        if (data.type === 'missing_person') {
            const daysMissing = data.days_missing;
            const statusBadge = findmeGetStatusBadge(data.status, data.is_minor);
            
            return `
                <div class="findme-popup-container">
                    <div class="findme-popup-header">
                        <img src="${data.photo_url || '/static/images/default_unknown.png'}" 
                             alt="${data.name}" 
                             class="findme-popup-image"
                             onerror="this.src='/static/images/default_unknown.png'">
                        ${statusBadge}
                    </div>
                    <div class="findme-popup-body">
                        <h3 class="findme-popup-name">${data.name}</h3>
                        <p class="findme-popup-info">
                            <i class="fas fa-user"></i> 
                            ${data.age ? data.age + ' years' : 'Age unknown'} • ${data.gender || 'Unknown'}
                        </p>
                        <p class="findme-popup-info">
                            <i class="fas fa-map-marker-alt"></i> 
                            ${data.last_seen_location}
                        </p>
                        <p class="findme-popup-info">
                            <i class="fas fa-clock"></i> 
                            ${daysMissing} days missing
                        </p>
                        ${data.case_number ? `<p class="findme-popup-case">Case #${data.case_number}</p>` : ''}
                        ${data.sighting_count > 0 ? `<p class="findme-popup-sightings"><i class="fas fa-eye"></i> ${data.sighting_count} verified sightings</p>` : ''}
                    </div>
                    <div class="findme-popup-footer">
                        <button class="findme-popup-btn" id="findme-view-details-${data.id}">
                            <i class="fas fa-info-circle"></i> View Full Details
                        </button>
                    </div>
                </div>
            `;
        } else if (data.type === 'sighting') {
            return `
                <div class="findme-popup-container">
                    <div class="findme-popup-body">
                        <h3 class="findme-popup-name">
                            <i class="fas fa-eye"></i> Sighting Report
                        </h3>
                        <p class="findme-popup-info">
                            <strong>Person:</strong> ${data.missing_person_name}
                        </p>
                        <p class="findme-popup-info">
                            <i class="fas fa-map-marker-alt"></i> 
                            ${data.sighting_location}
                        </p>
                        <p class="findme-popup-info">
                            <i class="fas fa-calendar"></i> 
                            ${new Date(data.sighting_date).toLocaleDateString()}
                        </p>
                        ${data.person_condition ? `<p class="findme-popup-info"><strong>Condition:</strong> ${data.person_condition}</p>` : ''}
                        <p class="findme-popup-description">${data.description}</p>
                    </div>
                </div>
            `;
        }
    }

    function findmeGetStatusBadge(status, isMinor) {
        if (isMinor) {
            return '<span class="findme-status-badge findme-status-minor">MINOR ALERT</span>';
        }
        
        const badges = {
            'missing': '<span class="findme-status-badge findme-status-missing">MISSING</span>',
            'found': '<span class="findme-status-badge findme-status-found">FOUND</span>',
            'investigating': '<span class="findme-status-badge findme-status-investigating">INVESTIGATING</span>',
            'closed': '<span class="findme-status-badge findme-status-closed">CLOSED</span>'
        };
        
        return badges[status] || '';
    }

    function findmeRenderMarkers(markers) {
        try {
            // Clear existing markers
            FINDME_STATE.markerClusterGroup.clearLayers();
            FINDME_STATE.markers = [];

            // Filter markers if minors only is enabled
            let filteredMarkers = markers;
            if (FINDME_STATE.currentFilters.showMinorsOnly) {
                filteredMarkers = markers.filter(m => m.is_minor);
            }

            // Create and add markers
            filteredMarkers.forEach(markerData => {
                try {
                    const marker = findmeCreateMarker(markerData);
                    FINDME_STATE.markers.push(marker);
                    
                    if (FINDME_STATE.currentFilters.showClusters) {
                        FINDME_STATE.markerClusterGroup.addLayer(marker);
                    } else {
                        marker.addTo(FINDME_STATE.map);
                    }
                } catch (error) {
                    console.error('Error creating marker:', error);
                }
            });

            // Fit bounds if markers exist
            if (FINDME_STATE.markers.length > 0) {
                const group = new L.featureGroup(FINDME_STATE.markers);
                FINDME_STATE.map.fitBounds(group.getBounds().pad(0.1));
            }

            console.log(`Rendered ${FINDME_STATE.markers.length} markers`);
        } catch (error) {
            console.error('Error rendering markers:', error);
            findmeShowToast('Error displaying markers', 'error');
        }
    }

    // ========================================
    // Statistics Rendering
    // ========================================
    
    function findmeRenderStatistics(stats) {
        try {
            document.getElementById('findmeStatActiveCases').textContent = stats.active_cases || 0;
            document.getElementById('findmeStatFound').textContent = stats.total_found || 0;
            document.getElementById('findmeStatInvestigating').textContent = stats.total_investigating || 0;
            document.getElementById('findmeStatMinors').textContent = stats.minors || 0;

            const hotspotsList = document.getElementById('findmeHotspotsList');
            if (stats.hotspots && stats.hotspots.length > 0) {
                hotspotsList.innerHTML = stats.hotspots.map(hotspot => `
                    <div class="findme-hotspot-item">
                        <span class="findme-hotspot-location">${hotspot.location}</span>
                        <span class="findme-hotspot-count">${hotspot.count} cases</span>
                    </div>
                `).join('');
            } else {
                hotspotsList.innerHTML = '<p class="findme-loading-text">No hotspot data available</p>';
            }
        } catch (error) {
            console.error('Error rendering statistics:', error);
        }
    }

    // ========================================
    // Person Details Modal
    // ========================================
    
    function findmeShowPersonModal(person) {
        try {
            const photosHtml = person.photos && person.photos.length > 0 
                ? person.photos.map(photo => `
                    <img src="${photo.url}" alt="${person.full_name}" class="findme-modal-photo">
                  `).join('')
                : `<img src="${person.photo_url || '/static/images/default_unknown.png'}" 
                       alt="${person.full_name}" class="findme-modal-photo">`;

            const sightingsHtml = person.sightings && person.sightings.length > 0
                ? `
                    <div class="findme-modal-section">
                        <h3><i class="fas fa-eye"></i> Verified Sightings (${person.sightings.length})</h3>
                        ${person.sightings.map(sighting => `
                            <div class="findme-sighting-card">
                                <p><strong>Location:</strong> ${sighting.location}</p>
                                <p><strong>Date:</strong> ${new Date(sighting.date).toLocaleDateString()}</p>
                                <p><strong>Description:</strong> ${sighting.description}</p>
                                ${sighting.condition ? `<p><strong>Condition:</strong> ${sighting.condition}</p>` : ''}
                            </div>
                        `).join('')}
                    </div>
                  `
                : '';

            FINDME_ELEMENTS.personModalBody.innerHTML = `
                <div class="findme-modal-header-content">
                    <h2>${person.full_name}</h2>
                    ${findmeGetStatusBadge(person.status, person.is_minor)}
                </div>

                <div class="findme-modal-photos">
                    ${photosHtml}
                </div>

                <div class="findme-modal-section">
                    <h3><i class="fas fa-user"></i> Personal Information</h3>
                    <div class="findme-info-grid">
                        <div class="findme-info-item">
                            <span class="findme-info-label">Age:</span>
                            <span class="findme-info-value">${person.age || 'Unknown'}</span>
                        </div>
                        <div class="findme-info-item">
                            <span class="findme-info-label">Gender:</span>
                            <span class="findme-info-value">${person.gender || 'Unknown'}</span>
                        </div>
                        <div class="findme-info-item">
                            <span class="findme-info-label">Height:</span>
                            <span class="findme-info-value">${person.height || 'Unknown'}</span>
                        </div>
                        <div class="findme-info-item">
                            <span class="findme-info-label">Weight:</span>
                            <span class="findme-info-value">${person.weight || 'Unknown'}</span>
                        </div>
                        <div class="findme-info-item">
                            <span class="findme-info-label">Hair Color:</span>
                            <span class="findme-info-value">${person.hair_color || 'Unknown'}</span>
                        </div>
                        <div class="findme-info-item">
                            <span class="findme-info-label">Eye Color:</span>
                            <span class="findme-info-value">${person.eye_color || 'Unknown'}</span>
                        </div>
                    </div>
                </div>

                <div class="findme-modal-section">
                    <h3><i class="fas fa-map-marker-alt"></i> Last Known Information</h3>
                    <p><strong>Last Seen:</strong> ${new Date(person.last_seen_date).toLocaleString()}</p>
                    <p><strong>Location:</strong> ${person.last_seen_location}</p>
                    ${person.last_seen_wearing ? `<p><strong>Wearing:</strong> ${person.last_seen_wearing}</p>` : ''}
                    ${person.circumstances ? `<p><strong>Circumstances:</strong> ${person.circumstances}</p>` : ''}
                </div>

                ${person.distinguishing_features ? `
                    <div class="findme-modal-section">
                        <h3><i class="fas fa-fingerprint"></i> Distinguishing Features</h3>
                        <p>${person.distinguishing_features}</p>
                    </div>
                ` : ''}

                ${sightingsHtml}

                <div class="findme-modal-section">
                    <h3><i class="fas fa-phone"></i> Contact Information</h3>
                    ${person.contact_name ? `<p><strong>Contact:</strong> ${person.contact_name}</p>` : ''}
                    ${person.contact_phone ? `<p><strong>Phone:</strong> <a href="tel:${person.contact_phone}">${person.contact_phone}</a></p>` : ''}
                    ${person.contact_email ? `<p><strong>Email:</strong> <a href="mailto:${person.contact_email}">${person.contact_email}</a></p>` : ''}
                    ${person.case_number ? `<p><strong>Case Number:</strong> ${person.case_number}</p>` : ''}
                </div>
            `;

            FINDME_ELEMENTS.personModal.classList.add('findme-active');
        } catch (error) {
            console.error('Error showing person modal:', error);
            findmeShowToast('Error displaying person details', 'error');
        }
    }

    function findmeClosePersonModal() {
        FINDME_ELEMENTS.personModal.classList.remove('findme-active');
    }

    // ========================================
    // UI Utilities
    // ========================================
    
    function findmeShowLoading(show) {
        if (show) {
            FINDME_ELEMENTS.loading.classList.remove('findme-hidden');
        } else {
            FINDME_ELEMENTS.loading.classList.add('findme-hidden');
        }
    }

    function findmeShowToast(message, type = 'info') {
        FINDME_ELEMENTS.toastMessage.textContent = message;
        FINDME_ELEMENTS.toast.className = 'findme-toast findme-' + type;
        FINDME_ELEMENTS.toast.classList.add('findme-show');

        setTimeout(() => {
            FINDME_ELEMENTS.toast.classList.remove('findme-show');
        }, FINDME_CONFIG.toastDuration);
    }

    function findmeUpdateResultsCounter(count) {
        FINDME_ELEMENTS.resultsCount.textContent = count;
    }

    function findmeTogglePanel(panel) {
        panel.classList.toggle('findme-active');
    }

    // ========================================
    // Filter Functions
    // ========================================
    
    function findmeApplyFilters() {
        FINDME_STATE.currentFilters.status = FINDME_ELEMENTS.statusFilter.value;
        FINDME_STATE.currentFilters.days = FINDME_ELEMENTS.daysFilter.value;
        FINDME_STATE.currentFilters.search = FINDME_ELEMENTS.searchInput.value.trim();
        FINDME_STATE.currentFilters.showSightings = FINDME_ELEMENTS.showSightingsCheckbox.checked;
        FINDME_STATE.currentFilters.showMinorsOnly = FINDME_ELEMENTS.showMinorsOnlyCheckbox.checked;
        FINDME_STATE.currentFilters.showClusters = FINDME_ELEMENTS.showClustersCheckbox.checked;

        findmeFetchMapMarkers();
        findmeShowToast('Filters applied', 'success');
    }

    function findmeResetFilters() {
        FINDME_ELEMENTS.statusFilter.value = 'missing';
        FINDME_ELEMENTS.daysFilter.value = '30';
        FINDME_ELEMENTS.searchInput.value = '';
        FINDME_ELEMENTS.showSightingsCheckbox.checked = true;
        FINDME_ELEMENTS.showMinorsOnlyCheckbox.checked = false;
        FINDME_ELEMENTS.showClustersCheckbox.checked = true;

        findmeApplyFilters();
    }

    // ========================================
    // Map Controls
    // ========================================
    
    function findmeLocateUser() {
        if ('geolocation' in navigator) {
            FINDME_ELEMENTS.locateMeBtn.classList.add('findme-spinning');
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    
                    FINDME_STATE.map.setView([lat, lng], 14);
                    
                    L.marker([lat, lng], {
                        icon: L.AwesomeMarkers.icon({
                            icon: 'crosshairs',
                            prefix: 'fa',
                            markerColor: 'blue'
                        })
                    }).addTo(FINDME_STATE.map)
                      .bindPopup('You are here')
                      .openPopup();
                    
                    FINDME_ELEMENTS.locateMeBtn.classList.remove('findme-spinning');
                    findmeShowToast('Location found', 'success');
                },
                (error) => {
                    FINDME_ELEMENTS.locateMeBtn.classList.remove('findme-spinning');
                    console.error('Geolocation error:', error);
                    findmeShowToast('Could not get your location', 'error');
                }
            );
        } else {
            findmeShowToast('Geolocation not supported', 'error');
        }
    }

    function findmeToggleFullscreen() {
        const container = document.querySelector('.findme-maps-container');
        
        if (!FINDME_STATE.isFullscreen) {
            if (container.requestFullscreen) {
                container.requestFullscreen();
            } else if (container.webkitRequestFullscreen) {
                container.webkitRequestFullscreen();
            } else if (container.msRequestFullscreen) {
                container.msRequestFullscreen();
            }
            FINDME_STATE.isFullscreen = true;
            FINDME_ELEMENTS.fullscreenBtn.innerHTML = '<i class="fas fa-compress"></i>';
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            FINDME_STATE.isFullscreen = false;
            FINDME_ELEMENTS.fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
        }
    }

    function findmeRefreshMap() {
        FINDME_ELEMENTS.refreshMapBtn.classList.add('findme-spinning');
        findmeFetchMapMarkers();
        findmeFetchStatistics();
        setTimeout(() => {
            FINDME_ELEMENTS.refreshMapBtn.classList.remove('findme-spinning');
        }, 1000);
    }

    // ========================================
    // Event Listeners
    // ========================================
    
    function findmeAttachEventListeners() {
        // Panel toggles
        FINDME_ELEMENTS.toggleFiltersBtn.addEventListener('click', () => {
            findmeTogglePanel(FINDME_ELEMENTS.filtersPanel);
        });

        FINDME_ELEMENTS.toggleStatsBtn.addEventListener('click', () => {
            findmeTogglePanel(FINDME_ELEMENTS.statsPanel);
            if (FINDME_ELEMENTS.statsPanel.classList.contains('findme-active')) {
                findmeFetchStatistics();
            }
        });

        // Filter controls
        FINDME_ELEMENTS.applyFiltersBtn.addEventListener('click', findmeApplyFilters);
        FINDME_ELEMENTS.resetFiltersBtn.addEventListener('click', findmeResetFilters);
        
        FINDME_ELEMENTS.searchClearBtn.addEventListener('click', () => {
            FINDME_ELEMENTS.searchInput.value = '';
            findmeApplyFilters();
        });

        FINDME_ELEMENTS.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                findmeApplyFilters();
            }
        });

        // Map controls
        FINDME_ELEMENTS.locateMeBtn.addEventListener('click', findmeLocateUser);
        FINDME_ELEMENTS.fullscreenBtn.addEventListener('click', findmeToggleFullscreen);
        FINDME_ELEMENTS.refreshMapBtn.addEventListener('click', findmeRefreshMap);

        // Modal controls
        FINDME_ELEMENTS.personModalClose.addEventListener('click', findmeClosePersonModal);
        FINDME_ELEMENTS.personModalOverlay.addEventListener('click', findmeClosePersonModal);

        // Toast close
        FINDME_ELEMENTS.toastClose.addEventListener('click', () => {
            FINDME_ELEMENTS.toast.classList.remove('findme-show');
        });

        // Escape key handler
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (FINDME_ELEMENTS.personModal.classList.contains('findme-active')) {
                    findmeClosePersonModal();
                }
            }
        });

        // Fullscreen change handler
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement) {
                FINDME_STATE.isFullscreen = false;
                FINDME_ELEMENTS.fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
            }
        });
    }

    // ========================================
    // Auto Update
    // ========================================
    
    function findmeStartAutoUpdate() {
        if (FINDME_STATE.updateTimer) {
            clearInterval(FINDME_STATE.updateTimer);
        }
        
        FINDME_STATE.updateTimer = setInterval(() => {
            findmeFetchMapMarkers();
            if (FINDME_ELEMENTS.statsPanel.classList.contains('findme-active')) {
                findmeFetchStatistics();
            }
        }, FINDME_CONFIG.updateInterval);
    }

    function findmeStopAutoUpdate() {
        if (FINDME_STATE.updateTimer) {
            clearInterval(FINDME_STATE.updateTimer);
            FINDME_STATE.updateTimer = null;
        }
    }

    // ========================================
    // Cleanup
    // ========================================
    
    function findmeCleanup() {
        findmeStopAutoUpdate();
        if (FINDME_STATE.map) {
            FINDME_STATE.map.remove();
        }
    }

    // ========================================
    // Main Initialization
    // ========================================
    
    function findmeInit() {
        try {
            console.log('Initializing FindMe Maps...');
            
            // Initialize map
            findmeInitializeMap();
            
            // Attach event listeners
            findmeAttachEventListeners();
            
            // Load initial data
            findmeFetchMapMarkers();
            
            // Start auto-update
            findmeStartAutoUpdate();
            
            console.log('FindMe Maps initialized successfully');
        } catch (error) {
            console.error('Initialization error:', error);
            findmeShowToast('Failed to initialize map', 'error');
        }
    }

    // ========================================
    // Page Load & Cleanup
    // ========================================
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', findmeInit);
    } else {
        findmeInit();
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', findmeCleanup);

})();