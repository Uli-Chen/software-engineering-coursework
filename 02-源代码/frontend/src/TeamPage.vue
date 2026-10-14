<script setup>
import { ref } from 'vue'
import { ArrowLeft, ArrowRight, BookOpen, Users } from 'lucide-vue-next'

const members = [
  { name: '陈辰', contribution: 20, role: '组长 · 规划与集成', work: '总体架构、进度协调、Docker 配置、代码集成与验收。', docs: '开发计划、小组工作总结、软件配置管理计划；汇总提交封面。' },
  { name: '董宇曦', contribution: 20, role: '需求分析与学生端', work: '课程目录、主选与备选、课表和成绩查询页面。', docs: '主写需求分析文档；补充设计文档中的学生端部分。' },
  { name: '刘根森', contribution: 20, role: '后端与数据库', work: '数据模型、选课接口、先修与冲突校验、并发名额控制、关闭选课。', docs: '主写设计文档，负责数据库、接口与核心业务流程。' },
  { name: '李怡宁', contribution: 20, role: '教师端与教务管理', work: '授课安排、学生名单、成绩录入、师生信息及授课资格管理。', docs: '补充需求分析与设计文档中的教师、教务模块。' },
  { name: '赵毓豪', contribution: 20, role: '测试与交付', work: '自动化测试、外部服务联调、故障恢复验证、部署检查和证据整理。', docs: '测试计划、测试报告、README；协助配置管理材料。' },
]
const stages = [
  { id: '01', name: '需求与分工', start: '2026-09-20', end: '2026-09-23', date: '09.20 — 09.23', milestone: '09.23 确认需求', owner: '陈辰 组织，董宇曦 主写需求，全员确认分工', goal: '明确系统范围、核心用例和五位成员的负责模块。', outputs: '开发计划、需求分析初稿、人员分工与验收清单。', checks: ['学生、教师、教务三类角色的核心用例明确。', '人员安排、接口边界和迭代计划经全组确认。'], next: '09.24 进入系统设计。' },
  { id: '02', name: '系统设计', start: '2026-09-24', end: '2026-09-28', date: '09.24 — 09.28', milestone: '09.28 确认设计', owner: '刘根森 主写设计，董宇曦、李怡宁 补充页面，陈辰 审核', goal: '确定 Vue、Flask 与数据库的结构，统一接口和业务规则。', outputs: '设计文档、数据库模型、接口清单与测试计划。', checks: ['选课、授课、成绩及关闭选课流程有对应设计。', '先修、冲突、容量和权限规则在前后端保持一致。'], next: '09.29 开始功能开发。' },
  { id: '03', name: '核心功能开发', start: '2026-09-29', end: '2026-10-06', date: '09.29 — 10.06', milestone: '10.06 集成版本', owner: '董宇曦、李怡宁 负责前端，刘根森 负责后端，陈辰 集成', goal: '完成三类角色的核心功能、初始化数据和容器启动。', outputs: '可运行系统、数据库结构、前后端接口与首轮测试记录。', checks: ['三类角色可登录并完成核心操作。', 'Docker Compose 能启动系统并保存业务数据。'], next: '10.07 进入联调与回归测试。' },
  { id: '04', name: '联调与交付准备', start: '2026-10-07', end: '2026-10-12', date: '10.07 — 10.12', milestone: '10.12 冻结交付', owner: '赵毓豪 主测，各成员修复负责模块，陈辰 汇总', goal: '逐条走查需求，修复问题、复测并完成演示与材料整理。', outputs: '测试报告、问题修复记录、五份个人总结与交付包。', checks: ['权限、选课事务、并发与外部服务异常测试通过。', '演示可完整运行，文档、源码和测试证据版本一致。'], next: '10.13 进行最终运行检查与提交。' },
  { id: '05', name: '运行检查与提交', start: '2026-10-13', end: '2026-10-13', date: '10.13', milestone: '10.13 最终提交', owner: '陈辰 汇总提交，全员参加验收', goal: '按计划完成最终运行检查及材料提交。', outputs: '最终程序、公共文档、五份个人总结及签名封面。', checks: ['组号、学号、实际贡献比例与本人签名齐全。', '现场程序、源码、文档和测试证据版本一致。'], next: '运行检查通过、材料核对齐全后提交。' },
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
        <div><h3>{{ member.name }}<span v-if="member.name==='陈辰'" class="badge green">组长</span></h3><p class="member-role">{{ member.role }}</p><p class="member-contribution">贡献比例 <strong>{{ member.contribution }}%</strong></p></div>
        <div><span class="team-field-label">负责功能</span><p>{{ member.work }}</p></div>
        <div><span class="team-field-label">文档产出</span><p>{{ member.docs }}</p></div>
      </article>
      <p class="team-note">每位成员另交个人工作总结。</p>
    </section>

    <section class="panel iteration-section" aria-labelledby="iteration-title">
      <div class="section-heading"><h2 id="iteration-title">进度与迭代计划</h2><span class="iteration-period">2026.09.20 — 2026.10.13</span></div>
      <div class="timeline-bounds"><span>项目启动 <time datetime="2026-09-20">09.20</time></span><span>最终提交 <time datetime="2026-10-13">10.13</time></span></div>
      <p class="iteration-hint">计划时间线 · 点击阶段查看任务与验收条件</p>
      <ol class="iteration-flow" aria-label="计划时间线：9月20日启动，需求与分工、系统设计、核心功能开发、联调与交付准备，10月13日最终提交">
        <li v-for="(stage,index) in stages" :key="stage.id">
          <button :class="['iteration-node',{selected:selected===index}]" :aria-pressed="selected===index" aria-controls="iteration-detail" @click="selected=index">
            <span class="iteration-node-top"><b>阶段 {{ stage.id }}</b></span>
            <span class="iteration-date">{{ stage.date }}</span><strong>{{ stage.name }}</strong>
            <span class="iteration-milestone">{{ stage.milestone }}</span>
          </button>
        </li>
      </ol>
      <section id="iteration-detail" class="iteration-detail" aria-live="polite" aria-atomic="true">
        <div class="iteration-detail-heading"><h3>{{ stages[selected].id }} · {{ stages[selected].name }}</h3><span>计划日期 {{ stages[selected].date }}</span></div>
        <p class="iteration-goal">{{ stages[selected].goal }}</p>
        <dl class="iteration-facts"><div><dt>起止时间</dt><dd><time :datetime="stages[selected].start">{{ stages[selected].start }}</time><span v-if="stages[selected].start!==stages[selected].end"> 至 <time :datetime="stages[selected].end">{{ stages[selected].end }}</time></span><span v-else>（当日）</span></dd></div><div><dt>交付节点</dt><dd>{{ stages[selected].milestone }}</dd></div><div><dt>负责人</dt><dd>{{ stages[selected].owner }}</dd></div><div><dt>阶段产出</dt><dd>{{ stages[selected].outputs }}</dd></div></dl>
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
.member-contribution{margin-top:6px}.member-contribution strong{color:var(--green);margin-left:6px}
.team-member p{font-size:13px;line-height:1.85}.team-field-label{display:none}
.team-note{font-size:12px;color:#6e7b6c;line-height:1.8;margin-top:18px}
.iteration-period{font-size:13px;color:#52664f;font-variant-numeric:tabular-nums}
.timeline-bounds{display:flex;justify-content:space-between;gap:16px;padding:14px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);font-size:13px;color:#52664f}.timeline-bounds time{font-size:20px;font-weight:600;margin-left:8px;color:var(--green);font-variant-numeric:tabular-nums}
.iteration-hint{font-size:12px;color:#6e7b6c;margin-top:14px}
.iteration-flow{list-style:none;padding:0;margin:22px 0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px}
.iteration-flow>li{position:relative;min-width:0;padding-top:24px}.iteration-flow>li::before{content:'';position:absolute;top:5px;left:0;right:-16px;height:2px;background:#cbd8c6}.iteration-flow>li:last-child::before{right:0}.iteration-flow>li::after{content:'';position:absolute;top:0;left:0;width:12px;height:12px;border:3px solid var(--green);border-radius:50%;background:#fff}
.iteration-node{width:100%;height:100%;text-align:left;border:1px solid #dfe5da;border-radius:8px;padding:16px 12px;background:#fafbf8}
.iteration-node.selected{border-color:var(--green);background:#edf4ed;box-shadow:0 0 0 1px var(--green)}
.iteration-node:focus-visible{outline:3px solid var(--green);outline-offset:4px}
.iteration-node:hover{border-color:var(--green)}.iteration-node-top{display:flex;align-items:center;justify-content:space-between;gap:6px}
.iteration-node-top>b{font-size:12px;color:#597650}.iteration-node>strong{display:block;font-size:14px;margin:10px 0;font-weight:600}
.iteration-date{display:block;color:var(--green);font-size:16px;font-weight:600;margin-top:12px;font-variant-numeric:tabular-nums;white-space:nowrap}.iteration-milestone{display:block;padding-top:10px;border-top:1px solid #dfe5da;color:#52664f;font-size:12px}
.iteration-detail{border:1px solid var(--line);border-radius:8px;padding:22px}
.iteration-detail-heading{display:flex;align-items:center;justify-content:space-between;gap:12px}.iteration-detail-heading h3{font-size:16px}.iteration-detail-heading>span{font-size:12px;color:#6b796c}
.iteration-goal{margin:12px 0 18px;font-size:14px}.iteration-facts{margin:0;display:grid;gap:10px}
.iteration-facts>div{display:grid;grid-template-columns:64px 1fr;gap:12px;font-size:13px}.iteration-facts dt{color:#6b796c}.iteration-facts dd{margin:0}
.iteration-checks{margin-top:20px;padding-top:18px;border-top:1px solid var(--line)}.iteration-checks h4{font-size:13px;margin:0 0 8px}.iteration-checks ul{margin:0;padding-left:19px;font-size:13px;line-height:1.9}
.iteration-next{display:flex;align-items:center;gap:7px;color:var(--green);font-size:13px;margin-top:16px}
@media(max-width:1000px){.team-column-head,.team-member{grid-template-columns:155px minmax(0,1fr) minmax(0,1fr);gap:18px}.iteration-flow{grid-template-columns:1fr;gap:16px}.iteration-flow>li{padding:0 0 0 26px}.iteration-flow>li::before{left:5px;right:auto;top:18px;bottom:-34px;width:2px;height:auto}.iteration-flow>li:last-child::before{display:none}.iteration-flow>li::after{top:18px}.iteration-node{display:grid;grid-template-columns:1fr 1fr;align-items:center;gap:10px 18px;padding:16px}.iteration-date{margin:0;text-align:right}.iteration-node>strong{margin:0}.iteration-milestone{border:0;padding:0;text-align:right}}
@media(max-width:640px){.team-page{padding:20px 16px 32px}.team-header{margin-bottom:28px}.team-title h1{font-size:25px}.team-assignment,.iteration-section{padding:20px}.team-column-head{display:none}.team-member{grid-template-columns:1fr;gap:12px}.team-field-label{display:block;color:#6b796c;font-size:12px;margin-bottom:3px}.team-member h3{font-size:16px}.team-member:first-of-type{padding-top:0}.iteration-section>.section-heading{align-items:flex-start;flex-direction:column;gap:8px}.timeline-bounds{font-size:12px;gap:8px}.timeline-bounds time{font-size:18px;margin-left:4px}.iteration-node{grid-template-columns:1fr;gap:10px}.iteration-date,.iteration-milestone{text-align:left}.iteration-node>strong{font-size:16px}.iteration-detail{padding:18px}.iteration-detail-heading{align-items:flex-start;flex-direction:column;gap:5px}.iteration-facts>div{grid-template-columns:1fr;gap:3px}.iteration-next{align-items:flex-start}.iteration-next svg{flex-shrink:0;margin-top:3px}}
</style>
