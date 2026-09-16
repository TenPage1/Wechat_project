// index.js
const app = getApp()

Page({
  data: {
    loading: true,
    error: '',
    raw: null,     // 完整原始返回
    info: null,    // 解析后的地址信息
    roads: [],     // 周边道路列表

    // 用户输入 & 历史记录
    longitude: '',
    latitude: '',
    savedRecord: null // 上次保存的记录
  },

  onLoad() {
    this.fetchData()
    this.loadSaved()   // 启动时调出上次保存的数据
  },

  // 输入框绑定
  onLongitudeInput(e) {
    this.setData({ longitude: e.detail.value })
  },
  onLatitudeInput(e) {
    this.setData({ latitude: e.detail.value })
  },

  // 保存用户输入到云数据库
  saveRecord() {
    const { longitude, latitude } = this.data
    if (!longitude || !latitude) {
      wx.showToast({ title: '请填写经纬度', icon: 'none' })
      return
    }
    wx.showLoading({ title: '保存中' })
    wx.cloud
      .callFunction({
        name: 'saveRecord',
        data: { content: `${longitude},${latitude}`, longitude, latitude }
      })
      .then((r) => {
        wx.hideLoading()
        const res = r.result || {}
        console.log('saveRecord 返回：', res)

        // 业务失败：弹窗显示云函数完整返回
        if (!res || res.code !== 0) {
        wx.showModal({
            title: '保存失败（云函数内部错误）',
            content: '完整返回：\n' + JSON.stringify(res),
          showCancel: false
      })
          return
        }

        // 业务成功
        wx.showToast({ title: res.msg || '已保存', icon: 'success' })
        this.setData({ savedRecord: { longitude, latitude } })
      })
      .catch((err) => {
        wx.hideLoading()
        // 把真实错误打印到控制台，并弹窗提示
        console.error('调用云函数失败：', err)
        wx.showModal({
          title: '保存失败',
          content: (err && err.errMsg) || JSON.stringify(err),
          showCancel: false
        })
      })
  },

  // 调出上次保存的数据（onLoad 自动调用）
  loadSaved() {
    this.readRecord(false)
  },

  // 读取云端数据：manual=true 表示用户点按钮触发（带提示）
  readRecord(manual = true) {
    if (manual) wx.showLoading({ title: '读取中' })
    wx.cloud
      .callFunction({ name: 'getRecord' })
      .then((r) => {
        const res = r.result || {}
        console.log('getRecord 返回：', res)
        if (manual) wx.hideLoading()

        // 情况一：云函数内部返回业务错误
        if (!res || res.code !== 0) {
        if (manual) {
            wx.showModal({
              title: '读取失败（云函数内部错误）',
              content: '完整返回：\n' + JSON.stringify(res),
            showCancel: false
          })
        }
          return
        }

        // 情况二：成功但无记录
        if (!res.data) {
          if (manual) wx.showToast({ title: '暂无记录', icon: 'none' })
          return
        }

        // 情况三：成功且有数据
        this.setData({
          savedRecord: res.data,
          longitude: res.data.longitude || '',
          latitude: res.data.latitude || ''
        })
        if (manual) wx.showToast({ title: '已读取上次数据', icon: 'success' })
      })
      .catch((err) => {
        // 情况四：云函数调用本身失败（未部署 / 网络 / 环境错误）
        if (manual) {
          wx.hideLoading()
          wx.showModal({
            title: '读取失败（调用云函数失败）',
            content:
              'errCode: ' + (err && err.errCode) + '\n' +
              'errMsg: ' + ((err && err.errMsg) || JSON.stringify(err)),
            showCancel: false
        })
  }
        console.error('读取记录失败', err)
      })
  },

  // 下拉刷新
  onPullDownRefresh() {
    app.globalData.apiData = null
    app.apiPromise = app.requestApi()
    this.fetchData().then(() => wx.stopPullDownRefresh())
  },

  fetchData() {
    this.setData({ loading: true, error: '' })
    return app.getApiData()
      .then((res) => {
        console.log('页面收到数据：', res)

        // 高德 regeo：status 为 "1" 才是成功
        if (!res || String(res.status) !== '1') {
          this.setData({
            loading: false,
            error: '接口返回异常：status=' + (res && res.status),
            raw: res
          })
          return
        }

        const d = res.data || {}
        this.setData({
          loading: false,
          raw: res,
          info: {
            country: d.country,
            province: d.province,
            city: d.city,
            district: d.district,
            desc: d.desc,
            pos: d.pos
          },
          roads: d.road_list || []
        })
      })
      .catch((err) => {
        this.setData({
          loading: false,
          error: '请求失败：' + (err.errMsg || JSON.stringify(err))
        })
      })
  }
})

