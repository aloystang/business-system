import React from 'react'
import { Link } from 'react-router-dom'

const sections = [
  {
    title: '策划咨询',
    description: '围绕项目前策，完成数据采集、筛选与测算。',
    items: [
      {
        title: '项目数据采集与结构化',
        desc: '采集项目基础信息并结构化存储。',
        to: '/intakes',
      },
      {
        title: '项目筛选模型',
        desc: '基于规则计算筛选评分与等级。',
        to: '/projects',
      },
      {
        title: '项目测算模型',
        desc: '资产方/内部/商户三类测算。',
        to: '/projects',
      },
    ],
  },
  {
    title: '委托管理',
    description: '委托管理相关能力（即将开放）。',
    items: [{ title: '即将开放', desc: '功能建设中', disabled: true }],
  },
  {
    title: '招商运营',
    description: '招商与运营能力（即将开放）。',
    items: [{ title: '即将开放', desc: '功能建设中', disabled: true }],
  },
  {
    title: '委托运营',
    description: '委托运营能力（即将开放）。',
    items: [{ title: '即将开放', desc: '功能建设中', disabled: true }],
  },
]

export default function Modules() {
  return (
    <div className="grid">
      <div className="card">
        <h2>功能模块首页</h2>
        <p>从这里进入各业务模块。当前重点在“策划咨询”模块。</p>
      </div>

      {sections.map((section) => (
        <div className="card" key={section.title}>
          <h3>{section.title}</h3>
          <p style={{ color: '#64748b' }}>{section.description}</p>
          <div className="grid two">
            {section.items.map((item) =>
              item.disabled ? (
                <div className="card muted" key={item.title}>
                  <h4>{item.title}</h4>
                  <p style={{ color: '#64748b' }}>{item.desc}</p>
                </div>
              ) : (
                <Link className="card" key={item.title} to={item.to}>
                  <h4>{item.title}</h4>
                  <p style={{ color: '#64748b' }}>{item.desc}</p>
                </Link>
              )
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
