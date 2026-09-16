// 云函数：从云数据库读取当前用户上次保存的记录
const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })
const db = cloud.database()

exports.main = async (event, context) => {
  const wxContext = cloud.getWXContext()
  const OPENID = wxContext.OPENID

  try {
    const res = await db
      .collection('user_input')
      .where({ _openid: OPENID })
      .orderBy('updateTime', 'desc')
      .limit(1)
      .get()

    if (res.data.length === 0) {
      return { code: 0, msg: '暂无记录', data: null }
    }
    return { code: 0, msg: '读取成功', data: res.data[0] }
  } catch (e) {
    return { code: -1, msg: '读取失败：' + e.message, data: null }
  }
}
