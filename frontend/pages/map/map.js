// pages/map/map.js —— 地图页（首页）
const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    openid: '',
    // 地图
    longitude: 121.196,
    latitude: 31.096,
    scale: 14,
    markers: [],
    // 点位
    points: [],
    // 当前选中的呼叫目标
    selectedPoint: null,
    // 呼叫后的订单
    currentOrder: null,
    // 轮询计时器
    polling: false,
    userLocation: null
  },

  onLoad() {
    this.login()
  },

  onShow() {
    // 每次进入都刷新点位
    if (this.data.openid) this.loadPoints()
  },

  onHide() {
    this.stopPolling()
  },

  onUnload() {
    this.stopPolling()
  },

  // ---------- 登录 ----------
  login() {
    wx.login({
      success: (res) => {
        api.post('/api/login', { code: res.code }).then((r) => {
          if (r.code === 0) {
            const openid = r.data.openid
            this.setData({ openid })
            wx.setStorageSync('openid', openid)
            this.loadPoints()
            this.getUserLocation()
          }
        }).catch((e) => {
          wx.showToast({ title: '登录失败', icon: 'none' })
          console.error(e)
        })
      }
    })
  },

  // ---------- 获取用户位置 ----------
  getUserLocation() {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        const loc = { longitude: res.longitude, latitude: res.latitude }
        this.setData({ userLocation: loc, longitude: res.longitude, latitude: res.latitude })
        this.loadPoints()
      },
      fail: () => {
        wx.showToast({ title: '未获取到位置', icon: 'none' })
      }
    })
  },

  // ---------- 拉取点位并渲染 marker ----------
  loadPoints() {
    api.get('/api/points/nearby').then((r) => {
      if (r.code !== 0) return
      let points = r.data || []
      // 若已知用户位置，按距离排序
      if (this.data.userLocation) {
        const u = this.data.userLocation
        points = points.map((p) => ({
          ...p,
          distance: Math.round(api.distanceMeters(u.longitude, u.latitude, p.longitude, p.latitude))
        }))
        points.sort((a, b) => a.distance - b.distance)
      }
      this.setData({ points, markers: this.buildMarkers(points) })
    }).catch((e) => console.error('拉取点位失败', e))
  },

  // 生成地图 marker
  buildMarkers(points) {
    const markers = points.map((p) => ({
      id: p.id,
      longitude: p.longitude,
      latitude: p.latitude,
      width: 30,
      height: 30,
      callout: {
        content: `${p.type === 'takeoff' ? '🛫' : '🅿'} ${p.name}`,
        display: 'BYCLICK',
        padding: 6,
        borderRadius: 6
      }
    }))
    // 用户位置
    if (this.data.userLocation) {
      markers.push({
        id: 99999,
        longitude: this.data.userLocation.longitude,
        latitude: this.data.userLocation.latitude,
        width: 24,
        height: 24,
        callout: { content: '我的位置', display: 'ALWAYS', padding: 4 }
      })
    }
    return markers
  },

  // 点击 marker
  onMarkerTap(e) {
    const id = e.detail.markerId
    const p = this.data.points.find((x) => x.id === id)
    if (p) {
      this.setData({ selectedPoint: p })
      wx.showToast({ title: p.name, icon: 'none' })
    }
  },

  // 点击列表中的点位
  selectPoint(e) {
    const idx = e.currentTarget.dataset.index
    const p = this.data.points[idx]
    if (!p) return
    this.setData({
      selectedPoint: p,
      longitude: p.longitude,
      latitude: p.latitude,
      scale: 16
    })
  },

  // ---------- 呼叫无人机 ----------
  callDrone() {
    const p = this.data.selectedPoint
    if (!p) {
      wx.showToast({ title: '请先在地图上选择目的地', icon: 'none' })
      return
    }
    if (p.type === 'takeoff') {
      wx.showModal({ title: '提示', content: '起飞点是无人机待命点，通常呼叫到停靠点哦', showCancel: false })
    }
    wx.showLoading({ title: '呼叫中' })
    api.post('/api/call', { openid: this.data.openid, to_point_id: p.id }).then((r) => {
      wx.hideLoading()
      if (r.code !== 0) {
        wx.showToast({ title: r.msg || '呼叫失败', icon: 'none' })
        return
      }
      wx.showToast({ title: '无人机已出发', icon: 'success' })
      this.setData({ currentOrder: r.data })
      this.startPolling(r.data.order_id)
    }).catch(() => {
      wx.hideLoading()
      wx.showToast({ title: '呼叫失败', icon: 'none' })
    })
  },

  // ---------- 扫码呼叫 ----------
  scanToCall() {
    wx.scanCode({
      success: (res) => {
        const qr = res.result
        api.get('/api/points/scan', { qr_id: qr }).then((r) => {
          if (r.code !== 0) {
            wx.showToast({ title: '二维码无效', icon: 'none' })
            return
          }
          this.callToPoint(r.data)
        })
      }
    })
  },

  callToPoint(point) {
    api.post('/api/call', { openid: this.data.openid, to_point_id: point.id }).then((r) => {
      if (r.code === 0) {
        wx.showToast({ title: '已呼叫到 ' + point.name, icon: 'none' })
        this.setData({ currentOrder: r.data, selectedPoint: point })
        this.startPolling(r.data.order_id)
      } else {
        wx.showToast({ title: r.msg || '呼叫失败', icon: 'none' })
      }
    })
  },

  // ---------- 轮询无人机位置 ----------
  startPolling(orderId) {
    this.stopPolling()
    this.setData({ polling: true })
    this.pollTimer = setInterval(() => {
      api.get('/api/order/status', { order_id: orderId }).then((r) => {
        if (r.code !== 0) return
        const order = r.data
        this.setData({ currentOrder: order })
        // 把无人机位置画到地图
        if (order.drone_lng && order.drone_lat) {
          const markers = this.buildMarkers(this.data.points).filter((m) => m.id !== 88888)
          markers.push({
            id: 88888,
            longitude: order.drone_lng,
            latitude: order.drone_lat,
            width: 30,
            height: 30,
            callout: { content: '🚁 无人机', display: 'ALWAYS', padding: 4 }
          })
          this.setData({ markers })
        }
        // 完成就停
        if (order.status === 'done' || order.status === 'arrived') {
          this.stopPolling()
          if (order.status === 'done') wx.showToast({ title: '无人机已到达', icon: 'success' })
        }
      })
    }, 1500)
  },

  stopPolling() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer)
      this.pollTimer = null
    }
    this.setData({ polling: false })
  },

  // 调试：手动触发一次模拟移动（无真实无人机时用）
  debugStep() {
    if (!this.data.currentOrder) return
    api.post('/api/debug/simulate_move', { order_id: this.data.currentOrder.order_id }).then(() => {
      this.startPolling(this.data.currentOrder.order_id)
    })
  }
})
