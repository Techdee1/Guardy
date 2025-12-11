// project/src/components/FloodEvacMap.jsx
// Mapbox GL JS component to draw flood polygon, nearest shelters, routes + direction arrows.
// Requires REACT_APP_MAPBOX_KEY (Mapbox access token)

import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_KEY || '<YOUR_MAPBOX_KEY>';

export default function FloodEvacMap({ floodGeoJson = null, routes = [], shelters = [], userLocation = null }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Initialize map
    mapRef.current = new mapboxgl.Map({
      container: containerRef.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: userLocation || (shelters[0] ? [Number(shelters[0].longitude), Number(shelters[0].latitude)] : [3.4, 6.5]),
      zoom: 12,
    });

    mapRef.current.on('load', () => {
      // Flood polygon display (if provided)
      if (floodGeoJson) {
        if (!mapRef.current.getSource('flood-zone')) {
          mapRef.current.addSource('flood-zone', { type: 'geojson', data: floodGeoJson });
          mapRef.current.addLayer({
            id: 'flood-fill',
            type: 'fill',
            source: 'flood-zone',
            paint: { 'fill-color': '#ff4d4f', 'fill-opacity': 0.25 }
          });
          mapRef.current.addLayer({
            id: 'flood-outline',
            type: 'line',
            source: 'flood-zone',
            paint: { 'line-color': '#b91c1c', 'line-width': 2 }
          });
        } else {
          mapRef.current.getSource('flood-zone').setData(floodGeoJson);
        }
      }

      // Shelters as GeoJSON source
      const shelterFeatures = (shelters || []).map(s => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: [Number(s.longitude), Number(s.latitude)] },
        properties: { id: s.id, name: s.name, distance: s.distance_km }
      }));

      if (!mapRef.current.getSource('shelters')) {
        mapRef.current.addSource('shelters', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: shelterFeatures }
        });

        mapRef.current.addLayer({
          id: 'shelter-symbols',
          type: 'symbol',
          source: 'shelters',
          layout: {
            'icon-image': 'marker-15',
            'icon-allow-overlap': true,
            'text-field': ['get', 'name'],
            'text-offset': [0, 1.2],
            'text-size': 12
          }
        });
      } else {
        mapRef.current.getSource('shelters').setData({ type: 'FeatureCollection', features: shelterFeatures });
      }

      // user marker
      if (userLocation) {
        new mapboxgl.Marker({ color: '#0ea5e9' })
          .setLngLat(userLocation)
          .setPopup(new mapboxgl.Popup().setText('Your location'))
          .addTo(mapRef.current);
      }

      // Add routes & arrow decorations
      routes.forEach((r, i) => {
        if (!r.route || !r.route.geometry) return;
        const routeId = `route-${i}`;

        // add source
        if (!mapRef.current.getSource(routeId)) {
          mapRef.current.addSource(routeId, {
            type: 'geojson',
            data: { type: 'Feature', geometry: r.route.geometry }
          });

          // add main line
          mapRef.current.addLayer({
            id: `${routeId}-line`,
            type: 'line',
            source: routeId,
            paint: { 'line-color': '#0ea5e9', 'line-width': 4 }
          });

          // create arrow image via canvas
          const canvas = document.createElement('canvas');
          canvas.width = 24; canvas.height = 24;
          const ctx = canvas.getContext('2d');
          ctx.fillStyle = '#0ea5e9';
          ctx.beginPath(); ctx.moveTo(6, 4); ctx.lineTo(18, 12); ctx.lineTo(6, 20); ctx.closePath(); ctx.fill();
          const dataUrl = canvas.toDataURL();

          // load image and add symbol-layer for arrows
          mapRef.current.loadImage(dataUrl, (err, img) => {
            if (err) {
              console.error('loadImage error', err);
              return;
            }
            const imgName = `arrow-${i}`;
            if (!mapRef.current.hasImage(imgName)) mapRef.current.addImage(imgName, img);

            mapRef.current.addLayer({
              id: `${routeId}-arrows`,
              type: 'symbol',
              source: routeId,
              layout: {
                'symbol-placement': 'line',
                'symbol-spacing': 80,
                'icon-image': imgName,
                'icon-size': 1,
                'icon-allow-overlap': true
              }
            });
          });
        } else {
          // update geometry if already exists
          const src = mapRef.current.getSource(routeId) as any;
          src.setData({ type: 'Feature', geometry: r.route.geometry });
        }
      });

      // Fit map bounds to show flood area + nearest shelter + user if available
      // Collect bbox coordinates
      const bounds = new mapboxgl.LngLatBounds();
      let added = false;
      if (floodGeoJson && floodGeoJson.type === 'FeatureCollection') {
        floodGeoJson.features.forEach((feat) => {
          if (feat.geometry.type === 'Polygon' || feat.geometry.type === 'MultiPolygon') {
            const coords = (feat.geometry.type === 'Polygon') ? feat.geometry.coordinates[0] : feat.geometry.coordinates.flat(1);
            coords.forEach((c) => bounds.extend([c[0], c[1]]));
            added = true;
          }
        });
      }
      if (!added && shelters.length > 0) {
        shelters.forEach(s => bounds.extend([Number(s.longitude), Number(s.latitude)]));
        added = true;
      }
      if (!added && userLocation) {
        bounds.extend(userLocation);
        added = true;
      }
      if (added) {
        mapRef.current.fitBounds(bounds, { padding: 40, maxZoom: 15 });
      }
    });

    return () => {
      mapRef.current?.remove();
    };
  }, [floodGeoJson, routes, shelters, userLocation]);

  return <div ref={containerRef} style={{ width: '100%', height: '520px', borderRadius: 8 }} />;
}
