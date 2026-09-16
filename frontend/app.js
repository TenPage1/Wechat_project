// app.js
App({
  // 页面在 onLoad 里通过 this.getApiData() 拿到数据（Promise）
  globalData: {
    apiData: null
  },

  onLaunch() {
    wx.cloud.init({
      env: "cloudbase-d6gddt1qn3e8665b5",
      traceUser: true
    })

    // 发起请求，并把 Promise 存起来供页面 await
    this.apiPromise = this.requestApi()
  },

  // 封装请求，返回 Promise，成功时把数据挂到 globalData
  requestApi() {
    return new Promise((resolve, reject) => {
      wx.request({
        url: 'https://ditu.amap.com/service/regeo',
        method: 'GET',
        data: {
          longitude: 121.049,   // 经度
          latitude: 31.315      // 纬度
        },
        success: (res) => {
          console.log('接口返回数据：', res.data)
          this.globalData.apiData = res.data
          resolve(res.data)
        },
        fail: (err) => {
          console.error('接口请求失败：', err)
          reject(err)
        }
      })
    })
  },

  // 页面调用：已有数据直接返回，否则等待请求完成
  getApiData() {
    if (this.globalData.apiData) {
      return Promise.resolve(this.globalData.apiData)
    }
    return this.apiPromise
  }
})

