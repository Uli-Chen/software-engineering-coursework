<script setup>
import { ref } from 'vue'
import { ArrowLeft, ArrowRight, BookOpen, Users } from 'lucide-vue-next'

const members = [
  { name: 'teammate0', role: '组长 · 规划与集成', work: '总体架构、进度协调、Docker 配置、代码集成与验收。', docs: '开发计划、小组工作总结、软件配置管理计划；汇总提交封面。' },
  { name: 'teammate1', role: '需求分析与学生端', work: '课程目录、主选与备选、课表和成绩查询页面。', docs: '主写需求分析文档；补充设计文档中的学生端部分。' },
  { name: 'teammate2', role: '后端与数据库', work: '数据模型、选课接口、先修与冲突校验、并发名额控制、关闭选课。', docs: '主写设计文档，负责数据库、接口与核心业务流程。' },
  { name: 'teammate3', role: '教师端与教务管理', work: '授课安排、学生名单、成绩录入、师生信息及授课资格管理。', docs: '补充需求分析与设计文档中的教师、教务模块。' },
  { name: 'teammate4', role: '测试与交付', work: '自动化测试、外部服务联调、故障恢复验证、部署检查和证据整理。', docs: '测试计划、测试报告、README；协助配置管理材料。' },
]
const stages = [
  { id: 'I1', name: '核心实现', date: '10 月 13 日', status: '当前版本', owner: '全员开发，teammate0 集成，teammate4 验证', goal: '完成核心功能、初始化数据和容器启动。', outputs: '可运行系统、数据库结构、首轮测试记录。', checks: ['三类角色可登录并完成核心操作。', '选课事务、权限与并发测试通过。'], next: '进入组员走查，逐条对照需求。' },
  { id: 'I2', name: '走查与修复', date: '10 月 14 日', status: '计划', owner: '各成员走查负责模块，teammate4 复测', goal: '核对用例和异常流程，修复问题并同步文档。', outputs: '问题清单、修复记录、更新后的需求与设计文档。', checks: ['每个核心用例和异常流程均完成核对。', '已修复问题复测通过，文档与程序一致。'], next: '通过走查后，进入答辩演练。' },
  { id: 'I3', name: '交付冻结', date: '10 月 15 日', status: '计划', owner: 'teammate0 组织，teammate4 检查环境，全员演练', goal: '完成答辩演练，整理并冻结交付版本。', outputs: '演示流程、提交文档、源码包与文件校验清单。', checks: ['在干净环境中成功启动并完整演示。', '无阻断缺陷，所有交付文件对应同一版本。'], next: '确认材料齐全，准备课程验收。' },
  { id: '验收', name: '运行检查与提交', date: '10 月 16 日', status: '计划', owner: 'teammate0 汇总提交，全员参加验收', goal: '完成现场运行检查及最终材料提交。', outputs: '最终程序、公共文档、五份个人总结及签名封面。', checks: ['组号、学号、实际贡献比例与本人签名齐全。', '现场程序、源码、文档和测试证据版本一致。'], next: '验收通过后完成提交。' },
]
const selected = ref(0)
</script>

<template>
  <main class="team-page">
    <header class="team-header">
      <a href="#" class="brand" aria-label="知课首页"><span class="brand-mark"><BookOpen /></span><b>知课</b></a>
      <a href="#" class="button secondary compact"><ArrowLeft :size="16" />返回首页</a>
    </header>
    <div class="team-title"><h1>团队说明</h1><span class="badge green"><Users :size="14" />五人小组</span></div>

    <section class="panel team-assignment" aria-labelledby="team-members-title">
      <div class="section-heading"><h2 id="team-members-title">人员安排</h2><span class="muted small">按模块负责，组长统一集成</span></div>
      <div class="team-column-head" aria-hidden="true"><span>成员 / 职责</span><span>负责功能</span><span>文档产出</span></div>
      <article v-for="member in members" :key="member.name" class="team-member">
        <div><h3>{{ member.name }}<span v-if="member.name==='teammate0'" class="badge green">组长</span></h3><p class="member-role">{{ member.role }}</p></div>
        <div><span class="team-field-label">负责功能</span><p>{{ member.work }}</p></div>
        <div><span class="team-field-label">文档产出</span><p>{{ member.docs }}</p></div>
      </article>
      <p class="team-note">每位成员另交个人工作总结。以上为拟定分工，实际贡献与签名由成员本人确认。</p>
    </section>

    <section class="panel iteration-section" aria-labelledby="iteration-title">
      <div class="section-heading"><h2 id="iteration-title">进度与迭代计划</h2><span class="muted small">2026 年 10 月 13 日 — 16 日</span></div>
      <p class="iteration-hint">点击阶段查看任务和验收条件；后续阶段为计划安排。</p>
      <ol class="iteration-flow" aria-label="迭代流程：核心实现、走查与修复、交付冻结、运行检查与提交">
        <li v-for="(stage,index) in stages" :key="stage.id">
          <button :class="['iteration-node',{selected:selected===index}]" :aria-pressed="selected===index" aria-controls="iteration-detail" @click="selected=index">
            <span class="iteration-node-top"><b>{{ stage.id }}</b><span :class="['badge',index===0?'green':'gray']">{{ stage.status }}</span></span>
            <strong>{{ stage.name }}</strong><span class="iteration-date">{{ stage.date }}</span>
          </button>
          <ArrowRight v-if="index<stages.length-1" class="iteration-arrow" :size="20" aria-hidden="true" />
        </li>
      </ol>
      <section id="iteration-detail" class="iteration-detail" aria-live="polite" aria-atomic="true">
        <div class="iteration-detail-heading"><h3>{{ stages[selected].id }} · {{ stages[selected].name }}</h3><span>{{ stages[selected].date }}</span></div>
        <p class="iteration-goal">{{ stages[selected].goal }}</p>
        <dl class="iteration-facts"><div><dt>负责人</dt><dd>{{ stages[selected].owner }}</dd></div><div><dt>阶段产出</dt><dd>{{ stages[selected].outputs }}</dd></div></dl>
        <div class="iteration-checks"><h4>验收条件</h4><ul><li v-for="check in stages[selected].checks" :key="check">{{ check }}</li></ul></div>
        <p class="iteration-next"><ArrowRight :size="16" />{{ stages[selected].next }}</p>
      </section>
      <p class="team-note">发现问题 → 修复 → 复测通过 → 继续下一阶段。</p>
    </section>
  </main>
</template>

<style scoped>
.team-page{max-width:1160px;margin:0 auto;padding:28px 32px 48px}
.team-header,.team-title{display:flex;align-items:center;justify-content:space-between;gap:16px}
.team-header{margin-bottom:38px}.team-title{margin-bottom:24px;justify-content:flex-start}
.team-title h1{font-size:28px}.team-title>.badge{gap:7px;font-size:12px}
.team-assignment,.iteration-section{padding:26px}
.team-column-head,.team-member{display:grid;grid-template-columns:190px minmax(0,1fr) minmax(0,1fr);gap:28px}
.team-column-head{padding:12px 0;color:#6b796c;font-size:12px;border-bottom:1px solid var(--line)}
.team-member{padding:20px 0;border-bottom:1px solid var(--line);align-items:start}
.team-member h3{display:flex;align-items:center;gap:8px;font-size:15px}.member-role{color:#647660;margin-top:7px}
.team-member p{font-size:13px;line-height:1.85}.team-field-label{display:none}
.team-note{font-size:12px;color:#6e7b6c;line-height:1.8;margin-top:18px}
.iteration-hint{font-size:12px;color:#6e7b6c;margin-top:-8px}
.iteration-flow{list-style:none;padding:0;margin:22px 0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:30px}
.iteration-flow>li{position:relative;min-width:0}.iteration-node{width:100%;height:100%;text-align:left;border:1px solid #dfe5da;border-radius:8px;padding:17px;background:#fafbf8}
.iteration-node.selected{border-color:var(--green);background:#edf4ed;box-shadow:0 0 0 1px var(--green)}
.iteration-node:hover{border-color:var(--green)}.iteration-node-top{display:flex;align-items:center;justify-content:space-between;gap:6px}
.iteration-node-top>b{font-size:12px;color:#597650}.iteration-node>strong{display:block;font-size:15px;margin:15px 0 5px;font-weight:600}
.iteration-date{color:#68785e;font-size:12px}.iteration-arrow{position:absolute;right:-25px;top:50%;transform:translateY(-50%);color:#90a288}
.iteration-detail{border:1px solid var(--line);border-radius:8px;padding:22px}
.iteration-detail-heading{display:flex;align-items:center;justify-content:space-between;gap:12px}.iteration-detail-heading h3{font-size:16px}.iteration-detail-heading>span{font-size:12px;color:#6b796c}
.iteration-goal{margin:12px 0 18px;font-size:14px}.iteration-facts{margin:0;display:grid;gap:10px}
.iteration-facts>div{display:grid;grid-template-columns:64px 1fr;gap:12px;font-size:13px}.iteration-facts dt{color:#6b796c}.iteration-facts dd{margin:0}
.iteration-checks{margin-top:20px;padding-top:18px;border-top:1px solid var(--line)}.iteration-checks h4{font-size:13px;margin:0 0 8px}.iteration-checks ul{margin:0;padding-left:19px;font-size:13px;line-height:1.9}
.iteration-next{display:flex;align-items:center;gap:7px;color:var(--green);font-size:13px;margin-top:16px}
@media(max-width:900px){.team-column-head,.team-member{grid-template-columns:155px minmax(0,1fr) minmax(0,1fr);gap:18px}.iteration-flow{grid-template-columns:1fr;gap:28px}.iteration-arrow{top:auto;right:50%;bottom:-24px;transform:translateX(50%) rotate(90deg)}.iteration-node{display:grid;grid-template-columns:120px 1fr auto;align-items:center;gap:18px}.iteration-node>strong{margin:0}}
@media(max-width:640px){.team-page{padding:20px 16px 32px}.team-header{margin-bottom:28px}.team-title h1{font-size:25px}.team-assignment,.iteration-section{padding:20px}.team-column-head{display:none}.team-member{grid-template-columns:1fr;gap:12px}.team-field-label{display:block;color:#6b796c;font-size:12px;margin-bottom:3px}.team-member h3{font-size:16px}.team-member:first-of-type{padding-top:0}.iteration-node{grid-template-columns:1fr;gap:10px}.iteration-node>strong{font-size:16px}.iteration-detail{padding:18px}.iteration-detail-heading{align-items:flex-start;flex-direction:column;gap:5px}.iteration-facts>div{grid-template-columns:1fr;gap:3px}.iteration-next{align-items:flex-start}.iteration-next svg{flex-shrink:0;margin-top:3px}}
</style>
