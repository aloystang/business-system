import React, { useEffect, useRef, useState } from 'react'
import { DEFAULT_AMAP_CENTER, loadAmapSdk } from '../lib/amap'

const AMAP_JS_KEY = import.meta.env.VITE_AMAP_JS_KEY || ''
const DEFAULT_CITY = import.meta.env.VITE_MAP_DEFAULT_CITY || '重庆市'

function normalizePoint(point) {
  if (!point) return null
  const longitude = Number(point.longitude)
  const latitude = Number(point.latitude)
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) return null
  return {
    longitude,
    latitude,
    address: point.address || '',
    city: point.city || '',
    district: point.district || '',
  }
}

function formatPoint(point) {
  if (!point) return ''
  const longitude = Number(point.longitude)
  const latitude = Number(point.latitude)
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) return ''
  return `${longitude.toFixed(6)}, ${latitude.toFixed(6)}`
}

export default function MapPointPickerModal({ open, initialPoint, onClose, onConfirm }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const geocoderRef = useRef(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedPoint, setSelectedPoint] = useState(normalizePoint(initialPoint))
  const [resolvingAddress, setResolvingAddress] = useState(false)

  useEffect(() => {
    if (!open) return
    setSelectedPoint(normalizePoint(initialPoint))
  }, [open, initialPoint])

  useEffect(() => {
    if (!open) return
    let disposed = false
    setError('')
    setLoading(true)

    loadAmapSdk(AMAP_JS_KEY)
      .then((AMap) => {
        if (disposed || !containerRef.current) return
        const normalizedInitial = normalizePoint(initialPoint)
        const center = normalizedInitial
          ? [normalizedInitial.longitude, normalizedInitial.latitude]
          : DEFAULT_AMAP_CENTER
        const map = new AMap.Map(containerRef.current, {
          zoom: 12,
          center,
          mapStyle: 'amap://styles/normal',
        })
        map.addControl(new AMap.Scale())
        if (DEFAULT_CITY) {
          map.setCity(DEFAULT_CITY)
        }
        geocoderRef.current = new AMap.Geocoder({})

        const setMarker = (lng, lat) => {
          if (!markerRef.current) {
            markerRef.current = new AMap.Marker({
              position: [lng, lat],
              offset: new AMap.Pixel(-8, -8),
              content: '<div class="dash-map-marker merchant"></div>',
            })
            map.add(markerRef.current)
          } else {
            markerRef.current.setPosition([lng, lat])
          }
        }

        if (normalizedInitial) {
          setMarker(normalizedInitial.longitude, normalizedInitial.latitude)
        }

        map.on('click', (event) => {
          const lng = Number(event.lnglat?.lng)
          const lat = Number(event.lnglat?.lat)
          if (!Number.isFinite(lng) || !Number.isFinite(lat)) return
          setMarker(lng, lat)
          setSelectedPoint((prev) => ({
            longitude: lng,
            latitude: lat,
            address: prev?.address || '',
            city: prev?.city || '',
            district: prev?.district || '',
          }))
          const geocoder = geocoderRef.current
          if (!geocoder) return
          setResolvingAddress(true)
          geocoder.getAddress([lng, lat], (status, result) => {
            if (disposed) return
            setResolvingAddress(false)
            if (status !== 'complete' || !result?.regeocode) return
            const component = result.regeocode.addressComponent || {}
            const cityValue = Array.isArray(component.city)
              ? component.city[0] || component.province || ''
              : component.city || component.province || ''
            setSelectedPoint({
              longitude: lng,
              latitude: lat,
              address: result.regeocode.formattedAddress || '',
              city: cityValue,
              district: component.district || '',
            })
          })
        })

        mapRef.current = map
      })
      .catch((err) => setError(err.message || '地图加载失败'))
      .finally(() => setLoading(false))

    return () => {
      disposed = true
      if (mapRef.current) {
        mapRef.current.destroy()
        mapRef.current = null
      }
      markerRef.current = null
      geocoderRef.current = null
    }
  }, [open])

  if (!open) return null

  return (
    <div className="dash-modal-mask" role="dialog" aria-modal="true">
      <div className="dash-modal">
        <div className="dash-modal-header">
          <h3>地图选点</h3>
          <button className="dash-icon-btn" type="button" onClick={onClose}>
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        {error ? (
          <div className="notice">{error}</div>
        ) : (
          <div className="dash-modal-map" ref={containerRef}>
            {loading && <div className="dash-map-empty overlay">地图加载中...</div>}
          </div>
        )}
        <div className="dash-modal-footer">
          <div className="dash-helper">
            {selectedPoint
              ? `已选择：${formatPoint(selectedPoint)}${
                  selectedPoint.address ? ` · ${selectedPoint.address}` : ''
                }`
              : '点击地图选择位置'}
            {resolvingAddress && <span>（正在解析地址）</span>}
          </div>
          <div className="dash-modal-actions">
            <button className="dash-btn secondary" type="button" onClick={onClose}>
              取消
            </button>
            <button
              className="dash-btn primary"
              type="button"
              onClick={() => selectedPoint && onConfirm(selectedPoint)}
              disabled={!selectedPoint}
            >
              使用该位置
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
