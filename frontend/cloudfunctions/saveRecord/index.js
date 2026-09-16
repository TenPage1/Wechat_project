// 云函数：保存用户输入到云数据库
const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })
const db = cloud.database()

exports.main = async (event, context) => {
  const wxContext = cloud.getWXContext()
  const OPENID = wxContext.OPENID

  const { content, longitude, latitude } = event

  try {
    // 同一个用户只保留一条记录：有则更新，无则新增
    const col = db.collection('user_input')
    const exist = await col.where({ _openid: OPENID }).get()

    const data = {
      content: content || '',
      longitude: longitude || '',
      latitude: latitude || '',
      updateTime: db.serverDate()
    }

    if (exist.data.length > 0) {
      await col.doc(exist.data[0]._id).update({ data })
      return { code: 0, msg: '更新成功', action: 'update' }
    } else {
      await col.add({ data: { ...data, _openid: OPENID } })
      return { code: 0, msg: '保存成功', action: 'add' }
    }
  } catch (e) {
    return { code: -1, msg: '保存失败：' + e.message }
  }
}
