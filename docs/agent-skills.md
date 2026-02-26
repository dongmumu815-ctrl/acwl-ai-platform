# Agent Skills

Agent Skills 是扩展 Claude 功能的模块化能力。每个 Skill 包含指令、元数据和可选资源（脚本、模板），Claude 在相关时会自动使用这些资源。

---

## 为什么使用 Skills

Skills 是可重用的、基于文件系统的资源，为 Claude 提供特定领域的专业知识：工作流、上下文和最佳实践，将通用代理转变为专家。与提示不同（提示是对话级别的一次性任务指令），Skills 按需加载，无需在多个对话中重复提供相同的指导。

**主要优势**：
- **专业化 Claude**：为特定领域的任务定制功能
- **减少重复**：创建一次，自动使用
- **组合功能**：结合 Skills 构建复杂工作流

<Note>
有关 Agent Skills 的架构和实际应用的深入讨论，请阅读我们的工程博客：[使用 Agent Skills 为真实世界装备代理](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)。
</Note>

## 使用 Skills

Anthropic 为常见文档任务（PowerPoint、Excel、Word、PDF）提供预构建的 Agent Skills，您也可以创建自己的自定义 Skills。两者的工作方式相同。Claude 在与您的请求相关时会自动使用它们。

**预构建的 Agent Skills** 可供 claude.ai 上的所有用户和通过 Claude API 使用。请参阅下面的[可用 Skills](#available-skills) 部分了解完整列表。

**自定义 Skills** 让您打包领域专业知识和组织知识。它们在 Claude 的所有产品中都可用：在 Claude Code 中创建它们、通过 API 上传它们，或在 claude.ai 设置中添加它们。

<Note>
**开始使用：**
- 对于预构建的 Agent Skills：请参阅[快速入门教程](/docs/zh-CN/agents-and-tools/agent-skills/quickstart)，开始在 API 中使用 PowerPoint、Excel、Word 和 PDF skills
- 对于自定义 Skills：请参阅 [Agent Skills 食谱](https://github.com/anthropics/claude-cookbooks/tree/main/skills)，了解如何创建您自己的 Skills
</Note>

## Skills 如何工作

Skills 利用 Claude 的虚拟机环境提供超越仅使用提示可能实现的功能。Claude 在具有文件系统访问权限的虚拟机中运行，允许 Skills 作为包含指令、可执行代码和参考资料的目录存在，组织方式就像您为新团队成员创建的入职指南。

这种基于文件系统的架构支持**渐进式披露**：Claude 按需分阶段加载信息，而不是预先消耗上下文。

### 三种 Skill 内容类型，三个加载级别

Skills 可以包含三种类型的内容，每种在不同时间加载：

### 第 1 级：元数据（始终加载）

**内容类型：指令**。Skill 的 YAML 前置数据提供发现信息：

```yaml
---
name: pdf-processing
description: 从 PDF 文件中提取文本和表格、填充表单、合并文档。在处理 PDF 文件或用户提及 PDF、表单或文档提取时使用。
---
```

Claude 在启动时加载此元数据并将其包含在系统提示中。这种轻量级方法意味着您可以安装许多 Skills 而不会产生上下文成本；Claude 只知道每个 Skill 的存在以及何时使用它。

### 第 2 级：指令（触发时加载）

**内容类型：指令**。SKILL.md 的主体包含程序知识：工作流、最佳实践和指导：

````markdown
# PDF 处理

## 快速入门

使用 pdfplumber 从 PDF 中提取文本：

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

有关高级表单填充，请参阅 [FORMS.md](FORMS.md)。
````

当您请求与 Skill 描述匹配的内容时，Claude 通过 bash 从文件系统读取 SKILL.md。只有这样，此内容才会进入上下文窗口。

### 第 3 级：资源和代码（按需加载）

**内容类型：指令、代码和资源**。Skills 可以捆绑其他材料：

```
pdf-skill/
├── SKILL.md (主要指令)
├── FORMS.md (表单填充指南)
├── REFERENCE.md (详细 API 参考)
└── scripts/
    └── fill_form.py (实用脚本)
```

**指令**：包含专业指导和工作流的其他 markdown 文件（FORMS.md、REFERENCE.md）

**代码**：Claude 通过 bash 运行的可执行脚本（fill_form.py、validate.py）；脚本提供确定性操作而不消耗上下文

**资源**：参考资料，如数据库架构、API 文档、模板或示例

Claude 仅在引用时访问这些文件。文件系统模型意味着每种内容类型都有不同的优势：指令用于灵活指导，代码用于可靠性，资源用于事实查询。

| 级别 | 加载时间 | 令牌成本 | 内容 |
|---|---|---|---|
| **第 1 级：元数据** | 始终（启动时） | 每个 Skill 约 100 个令牌 | YAML 前置数据中的 `name` 和 `description` |
| **第 2 级：指令** | 触发 Skill 时 | 不到 5k 个令牌 | 包含指令和指导的 SKILL.md 主体 |
| **第 3 级+：资源** | 按需 | 实际上无限制 | 通过 bash 执行的捆绑文件，不将内容加载到上下文中 |

渐进式披露确保任何给定时间只有相关内容占据上下文窗口。

### Skills 架构

Skills 在代码执行环境中运行，Claude 具有文件系统访问、bash 命令和代码执行功能。可以这样想：Skills 作为虚拟机上的目录存在，Claude 使用与您在计算机上导航文件相同的 bash 命令与它们交互。

![Agent Skills 架构 - 显示 Skills 如何与代理的配置和虚拟机集成](/docs/images/agent-skills-architecture.png)

**Claude 如何访问 Skill 内容：**

触发 Skill 时，Claude 使用 bash 从文件系统读取 SKILL.md，将其指令带入上下文窗口。如果这些指令引用其他文件（如 FORMS.md 或数据库架构），Claude 也会使用其他 bash 命令读取这些文件。当指令提及可执行脚本时，Claude 通过 bash 运行它们并仅接收输出（脚本代码本身永远不会进入上下文）。

**此架构支持的功能：**

**按需文件访问**：Claude 仅读取每个特定任务所需的文件。Skill 可以包含数十个参考文件，但如果您的任务只需要销售架构，Claude 仅加载该文件。其余文件保留在文件系统上，消耗零令牌。

**高效的脚本执行**：当 Claude 运行 `validate_form.py` 时，脚本的代码永远不会加载到上下文窗口中。仅脚本的输出（如"验证通过"或特定错误消息）消耗令牌。这使脚本比让 Claude 即时生成等效代码要高效得多。

**捆绑内容没有实际限制**：因为文件在访问前不消耗上下文，Skills 可以包含全面的 API 文档、大型数据集、广泛的示例或任何您需要的参考资料。对于未使用的捆绑内容没有上下文成本。

这种基于文件系统的模型是使渐进式披露工作的原因。Claude 导航您的 Skill 就像您参考入职指南的特定部分一样，访问每个任务所需的确切内容。

### 示例：加载 PDF 处理 skill

以下是 Claude 如何加载和使用 PDF 处理 skill 的方式：

1. **启动**：系统提示包括：`PDF 处理 - 从 PDF 文件中提取文本和表格、填充表单、合并文档`
2. **用户请求**：「从此 PDF 中提取文本并总结」
3. **Claude 调用**：`bash: read pdf-skill/SKILL.md` → 指令加载到上下文中
4. **Claude 确定**：不需要表单填充，因此不读取 FORMS.md
5. **Claude 执行**：使用 SKILL.md 中的指令完成任务

![Skills 加载到上下文窗口 - 显示 skill 元数据和内容的渐进式加载](/docs/images/agent-skills-context-window.png)

该图表显示：
1. 预加载系统提示和 skill 元数据的默认状态
2. Claude 通过 bash 读取 SKILL.md 触发 skill
3. Claude 根据需要可选地读取其他捆绑文件，如 FORMS.md
4. Claude 继续执行任务

这种动态加载确保只有相关的 skill 内容占据上下文窗口。

## Skills 工作的地方

Skills 在 Claude 的代理产品中可用：

### Claude API

Claude API 支持预构建的 Agent Skills 和自定义 Skills。两者的工作方式相同：在 `container` 参数中指定相关的 `skill_id` 以及代码执行工具。

**前提条件**：通过 API 使用 Skills 需要三个 beta 标头：
- `code-execution-2025-08-25` - Skills 在代码执行容器中运行
- `skills-2025-10-02` - 启用 Skills 功能
- `files-api-2025-04-14` - 上传/下载文件到/从容器所需

通过引用其 `skill_id`（例如 `pptx`、`xlsx`）使用预构建的 Agent Skills，或通过 Skills API（`/v1/skills` 端点）创建和上传您自己的。自定义 Skills 在组织范围内共享。

要了解更多信息，请参阅[使用 Claude API 的 Skills](/docs/zh-CN/build-with-claude/skills-guide)。

### Claude Code

[Claude Code](https://code.claude.com/docs/overview) 仅支持自定义 Skills。

**自定义 Skills**：创建包含 SKILL.md 文件的目录形式的 Skills。Claude 自动发现并使用它们。

Claude Code 中的自定义 Skills 基于文件系统，不需要 API 上传。

要了解更多信息，请参阅[在 Claude Code 中使用 Skills](https://code.claude.com/docs/skills)。

### Claude Agent SDK

[Claude Agent SDK](/docs/zh-CN/agent-sdk/overview) 通过基于文件系统的配置支持自定义 Skills。

**自定义 Skills**：在 `.claude/skills/` 中创建包含 SKILL.md 文件的目录形式的 Skills。通过在 `allowed_tools` 配置中包含 `"Skill"` 来启用 Skills。

SDK 运行时会自动发现 Skills 中的 Skills。

要了解更多信息，请参阅 [SDK 中的 Agent Skills](/docs/zh-CN/agent-sdk/skills)。

### Claude.ai

[Claude.ai](https://claude.ai) 支持预构建的 Agent Skills 和自定义 Skills。

**预构建的 Agent Skills**：这些 Skills 在您创建文档时已在后台工作。Claude 使用它们而不需要任何设置。

**自定义 Skills**：通过设置 > 功能将您自己的 Skills 作为 zip 文件上传。在启用代码执行的 Pro、Max、Team 和 Enterprise 计划上可用。自定义 Skills 对每个用户是个人的；它们不在组织范围内共享，管理员无法集中管理。

要了解更多关于在 Claude.ai 中使用 Skills 的信息，请参阅 Claude 帮助中心中的以下资源：
- [什么是 Skills？](https://support.claude.com/en/articles/12512176-what-are-skills)
- [在 Claude 中使用 Skills](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [如何创建自定义 Skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [使用 Skills 教 Claude 您的工作方式](https://support.claude.com/en/articles/12580051-teach-claude-your-way-of-working-using-skills)

## Skill 结构

每个 Skill 都需要一个带有 YAML 前置数据的 `SKILL.md` 文件：

```yaml
---
name: your-skill-name
description: 简要描述此 Skill 的功能以及何时使用它
---

# 您的 Skill 名称

## 指令
[Claude 要遵循的清晰、分步指导]

## 示例
[使用此 Skill 的具体示例]
```

**必需字段**：`name` 和 `description`

**字段要求**：

`name`：
- 最多 64 个字符
- 只能包含小写字母、数字和连字符
- 不能包含 XML 标签
- 不能包含保留字：「anthropic」、「claude」

`description`：
- 必须非空
- 最多 1024 个字符
- 不能包含 XML 标签

`description` 应包括 Skill 的功能以及 Claude 何时应使用它。有关完整的创作指导，请参阅[最佳实践指南](/docs/zh-CN/agents-and-tools/agent-skills/best-practices)。

## 安全考虑

我们强烈建议仅从受信任的来源使用 Skills：您自己创建的或从 Anthropic 获得的。Skills 通过指令和代码为 Claude 提供新功能，虽然这使它们功能强大，但也意味着恶意 Skill 可以指导 Claude 以与 Skill 声称的目的不匹配的方式调用工具或执行代码。

<Warning>
如果您必须使用来自不受信任或未知来源的 Skill，请格外谨慎并在使用前彻底审计它。根据 Claude 在执行 Skill 时拥有的访问权限，恶意 Skills 可能导致数据泄露、未授权系统访问或其他安全风险。
</Warning>

**关键安全考虑**：
- **彻底审计**：查看 Skill 中捆绑的所有文件：SKILL.md、脚本、图像和其他资源。寻找异常模式，如意外的网络调用、文件访问模式或与 Skill 声称的目的不匹配的操作
- **外部来源有风险**：从外部 URL 获取数据的 Skills 特别有风险，因为获取的内容可能包含恶意指令。即使是可信的 Skills 如果其外部依赖项随时间变化也可能被破坏
- **工具滥用**：恶意 Skills 可以以有害方式调用工具（文件操作、bash 命令、代码执行）
- **数据泄露**：具有敏感数据访问权限的 Skills 可能被设计为向外部系统泄露信息
- **像安装软件一样对待**：仅从受信任的来源使用 Skills。在将 Skills 集成到具有敏感数据或关键操作访问权限的生产系统时要特别小心

## 可用 Skills

### 预构建的 Agent Skills

以下预构建的 Agent Skills 可立即使用：

- **PowerPoint (pptx)**：创建演示文稿、编辑幻灯片、分析演示文稿内容
- **Excel (xlsx)**：创建电子表格、分析数据、生成带图表的报告
- **Word (docx)**：创建文档、编辑内容、格式化文本
- **PDF (pdf)**：生成格式化的 PDF 文档和报告

这些 Skills 在 Claude API 和 claude.ai 上可用。请参阅[快速入门教程](/docs/zh-CN/agents-and-tools/agent-skills/quickstart)开始在 API 中使用它们。

### 自定义 Skills 示例

有关自定义 Skills 的完整示例，请参阅 [Skills 食谱](https://github.com/anthropics/claude-cookbooks/tree/main/skills)。

## 限制和约束

了解这些限制有助于您有效规划 Skills 部署。

### 跨平台可用性

**自定义 Skills 不会跨平台同步**。上传到一个平台的 Skills 不会自动在其他平台上可用：

- 上传到 Claude.ai 的 Skills 必须单独上传到 API
- 通过 API 上传的 Skills 在 Claude.ai 上不可用
- Claude Code Skills 基于文件系统，与 Claude.ai 和 API 分离

您需要为要使用 Skills 的每个平台单独管理和上传 Skills。

### 共享范围

Skills 根据使用位置有不同的共享模型：
- **Claude.ai**：仅限个人用户；每个团队成员必须单独上传
- **Claude API**：工作区范围；所有工作区成员可以访问上传的 Skills
- **Claude Code**：个人（`~/.claude/skills/`）或基于项目（`.claude/skills/`）

Claude.ai 目前不支持自定义 Skills 的集中管理员管理或组织范围分发。

### 运行时环境约束

Skills 在代码执行容器中运行，具有以下限制：

- **无网络访问**：Skills 无法进行外部 API 调用或访问互联网
- **无运行时包安装**：仅预安装的包可用。您无法在执行期间安装新包。
- **仅预配置的依赖项**：检查[代码执行工具文档](/docs/zh-CN/agents-and-tools/tool-use/code-execution-tool)了解可用包的列表

规划您的 Skills 在这些约束范围内工作。

## 后续步骤

<CardGroup cols={2}>
  <Card
    title="开始使用 Agent Skills"
    icon="graduation-cap"
    href="/docs/zh-CN/agents-and-tools/agent-skills/quickstart"
  >
    创建您的第一个 Skill
  </Card>
  <Card
    title="API 指南"
    icon="code"
    href="/docs/zh-CN/build-with-claude/skills-guide"
  >
    使用 Claude API 的 Skills
  </Card>
  <Card
    title="在 Claude Code 中使用 Skills"
    icon="terminal"
    href="https://code.claude.com/docs/skills"
  >
    在 Claude Code 中创建和管理自定义 Skills
  </Card>
  <Card
    title="在 Agent SDK 中使用 Skills"
    icon="cube"
    href="/docs/zh-CN/agent-sdk/skills"
  >
    在 TypeScript 和 Python 中以编程方式使用 Skills
  </Card>
  <Card
    title="创作最佳实践"
    icon="lightbulb"
    href="/docs/zh-CN/agents-and-tools/agent-skills/best-practices"
  >
    编写 Claude 可以有效使用的 Skills
  </Card>
</CardGroup>

# 在 API 中开始使用 Agent Skills

学习如何使用 Agent Skills 在 10 分钟内使用 Claude API 创建文档。

---

本教程向您展示如何使用 Agent Skills 创建 PowerPoint 演示文稿。您将学习如何启用 Skills、进行简单请求以及访问生成的文件。

## 前置条件

- [Anthropic API 密钥](/settings/keys)
- Python 3.7+ 或已安装 curl
- 对进行 API 请求的基本熟悉

## 什么是 Agent Skills？

预构建的 Agent Skills 通过专门的专业知识扩展 Claude 的功能，用于创建文档、分析数据和处理文件等任务。Anthropic 在 API 中提供以下预构建的 Agent Skills：

- **PowerPoint (pptx)**：创建和编辑演示文稿
- **Excel (xlsx)**：创建和分析电子表格
- **Word (docx)**：创建和编辑文档
- **PDF (pdf)**：生成 PDF 文档

<Note>
**想要创建自定义 Skills？** 请查看 [Agent Skills Cookbook](https://github.com/anthropics/claude-cookbooks/tree/main/skills) 以获取使用特定领域专业知识构建您自己的 Skills 的示例。
</Note>

## 步骤 1：列出可用的 Skills

首先，让我们看看有哪些可用的 Skills。我们将使用 Skills API 列出所有 Anthropic 管理的 Skills：

<CodeGroup>
```python Python
import anthropic

client = anthropic.Anthropic()

# List Anthropic-managed Skills
skills = client.beta.skills.list(
    source="anthropic",
    betas=["skills-2025-10-02"]
)

for skill in skills.data:
    print(f"{skill.id}: {skill.display_title}")
```

```typescript TypeScript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

// List Anthropic-managed Skills
const skills = await client.beta.skills.list({
  source: 'anthropic',
  betas: ['skills-2025-10-02']
});

for (const skill of skills.data) {
  console.log(`${skill.id}: ${skill.display_title}`);
}
```

```bash Shell
curl "https://api.anthropic.com/v1/skills?source=anthropic" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02"
```
</CodeGroup>

您会看到以下 Skills：`pptx`、`xlsx`、`docx` 和 `pdf`。

此 API 返回每个 Skill 的元数据：其名称和描述。Claude 在启动时加载此元数据以了解有哪些可用的 Skills。这是**渐进式披露**的第一个级别，其中 Claude 发现 Skills 而不加载其完整说明。

## 步骤 2：创建演示文稿

现在我们将使用 PowerPoint Skill 创建关于可再生能源的演示文稿。我们使用 Messages API 中的 `container` 参数指定 Skills：

<CodeGroup>
```python Python
import anthropic

client = anthropic.Anthropic()

# Create a message with the PowerPoint Skill
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {
                "type": "anthropic",
                "skill_id": "pptx",
                "version": "latest"
            }
        ]
    },
    messages=[{
        "role": "user",
        "content": "Create a presentation about renewable energy with 5 slides"
    }],
    tools=[{
        "type": "code_execution_20250825",
        "name": "code_execution"
    }]
)

print(response.content)
```

```typescript TypeScript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

// Create a message with the PowerPoint Skill
const response = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [
      {
        type: 'anthropic',
        skill_id: 'pptx',
        version: 'latest'
      }
    ]
  },
  messages: [{
    role: 'user',
    content: 'Create a presentation about renewable energy with 5 slides'
  }],
  tools: [{
    type: 'code_execution_20250825',
    name: 'code_execution'
  }]
});

console.log(response.content);
```

```bash Shell
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "container": {
      "skills": [
        {
          "type": "anthropic",
          "skill_id": "pptx",
          "version": "latest"
        }
      ]
    },
    "messages": [{
      "role": "user",
      "content": "Create a presentation about renewable energy with 5 slides"
    }],
    "tools": [{
      "type": "code_execution_20250825",
      "name": "code_execution"
    }]
  }'
```
</CodeGroup>

让我们分解每个部分的作用：

- **`container.skills`**：指定 Claude 可以使用哪些 Skills
- **`type: "anthropic"`**：表示这是 Anthropic 管理的 Skill
- **`skill_id: "pptx"`**：PowerPoint Skill 标识符
- **`version: "latest"`**：Skill 版本设置为最近发布的版本
- **`tools`**：启用代码执行（Skills 所需）
- **Beta 标头**：`code-execution-2025-08-25` 和 `skills-2025-10-02`

当您进行此请求时，Claude 会自动将您的任务与相关的 Skill 匹配。由于您要求演示文稿，Claude 确定 PowerPoint Skill 是相关的并加载其完整说明：这是渐进式披露的第二个级别。然后 Claude 执行 Skill 的代码来创建您的演示文稿。

## 步骤 3：下载创建的文件

演示文稿是在代码执行容器中创建的，并保存为文件。响应包括带有文件 ID 的文件引用。提取文件 ID 并使用 Files API 下载它：

<CodeGroup>
```python Python
# Extract file ID from response
file_id = None
for block in response.content:
    if block.type == 'tool_use' and block.name == 'code_execution':
        # File ID is in the tool result
        for result_block in block.content:
            if hasattr(result_block, 'file_id'):
                file_id = result_block.file_id
                break

if file_id:
    # Download the file
    file_content = client.beta.files.download(
        file_id=file_id,
        betas=["files-api-2025-04-14"]
    )

    # Save to disk
    with open("renewable_energy.pptx", "wb") as f:
        file_content.write_to_file(f.name)

    print(f"Presentation saved to renewable_energy.pptx")
```

```typescript TypeScript
// Extract file ID from response
let fileId: string | null = null;
for (const block of response.content) {
  if (block.type === 'tool_use' && block.name === 'code_execution') {
    // File ID is in the tool result
    for (const resultBlock of block.content) {
      if ('file_id' in resultBlock) {
        fileId = resultBlock.file_id;
        break;
      }
    }
  }
}

if (fileId) {
  // Download the file
  const fileContent = await client.beta.files.download(fileId, {
    betas: ['files-api-2025-04-14']
  });

  // Save to disk
  const fs = require('fs');
  fs.writeFileSync('renewable_energy.pptx', Buffer.from(await fileContent.arrayBuffer()));

  console.log('Presentation saved to renewable_energy.pptx');
}
```

```bash Shell
# Extract file_id from response (using jq)
FILE_ID=$(echo "$RESPONSE" | jq -r '.content[] | select(.type=="tool_use" and .name=="code_execution") | .content[] | select(.file_id) | .file_id')

# Download the file
curl "https://api.anthropic.com/v1/files/$FILE_ID/content" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: files-api-2025-04-14" \
  --output renewable_energy.pptx

echo "Presentation saved to renewable_energy.pptx"
```
</CodeGroup>

<Note>
有关处理生成文件的完整详细信息，请参阅 [代码执行工具文档](/docs/zh-CN/agents-and-tools/tool-use/code-execution-tool#retrieve-generated-files)。
</Note>

## 尝试更多示例

现在您已经使用 Skills 创建了第一个文档，请尝试这些变体：

### 创建电子表格

<CodeGroup>
```python Python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {
                "type": "anthropic",
                "skill_id": "xlsx",
                "version": "latest"
            }
        ]
    },
    messages=[{
        "role": "user",
        "content": "Create a quarterly sales tracking spreadsheet with sample data"
    }],
    tools=[{
        "type": "code_execution_20250825",
        "name": "code_execution"
    }]
)
```

```typescript TypeScript
const response = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [
      {
        type: 'anthropic',
        skill_id: 'xlsx',
        version: 'latest'
      }
    ]
  },
  messages: [{
    role: 'user',
    content: 'Create a quarterly sales tracking spreadsheet with sample data'
  }],
  tools: [{
    type: 'code_execution_20250825',
    name: 'code_execution'
  }]
});
```

```bash Shell
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "container": {
      "skills": [
        {
          "type": "anthropic",
          "skill_id": "xlsx",
          "version": "latest"
        }
      ]
    },
    "messages": [{
      "role": "user",
      "content": "Create a quarterly sales tracking spreadsheet with sample data"
    }],
    "tools": [{
      "type": "code_execution_20250825",
      "name": "code_execution"
    }]
  }'
```
</CodeGroup>

### 创建 Word 文档

<CodeGroup>
```python Python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {
                "type": "anthropic",
                "skill_id": "docx",
                "version": "latest"
            }
        ]
    },
    messages=[{
        "role": "user",
        "content": "Write a 2-page report on the benefits of renewable energy"
    }],
    tools=[{
        "type": "code_execution_20250825",
        "name": "code_execution"
    }]
)
```

```typescript TypeScript
const response = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [
      {
        type: 'anthropic',
        skill_id: 'docx',
        version: 'latest'
      }
    ]
  },
  messages: [{
    role: 'user',
    content: 'Write a 2-page report on the benefits of renewable energy'
  }],
  tools: [{
    type: 'code_execution_20250825',
    name: 'code_execution'
  }]
});
```

```bash Shell
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "container": {
      "skills": [
        {
          "type": "anthropic",
          "skill_id": "docx",
          "version": "latest"
        }
      ]
    },
    "messages": [{
      "role": "user",
      "content": "Write a 2-page report on the benefits of renewable energy"
    }],
    "tools": [{
      "type": "code_execution_20250825",
      "name": "code_execution"
    }]
  }'
```
</CodeGroup>

### 生成 PDF

<CodeGroup>
```python Python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {
                "type": "anthropic",
                "skill_id": "pdf",
                "version": "latest"
            }
        ]
    },
    messages=[{
        "role": "user",
        "content": "Generate a PDF invoice template"
    }],
    tools=[{
        "type": "code_execution_20250825",
        "name": "code_execution"
    }]
)
```

```typescript TypeScript
const response = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [
      {
        type: 'anthropic',
        skill_id: 'pdf',
        version: 'latest'
      }
    ]
  },
  messages: [{
    role: 'user',
    content: 'Generate a PDF invoice template'
  }],
  tools: [{
    type: 'code_execution_20250825',
    name: 'code_execution'
  }]
});
```

```bash Shell
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "container": {
      "skills": [
        {
          "type": "anthropic",
          "skill_id": "pdf",
          "version": "latest"
        }
      ]
    },
    "messages": [{
      "role": "user",
      "content": "Generate a PDF invoice template"
    }],
    "tools": [{
      "type": "code_execution_20250825",
      "name": "code_execution"
    }]
  }'
```
</CodeGroup>

## 后续步骤

现在您已经使用了预构建的 Agent Skills，您可以：

<CardGroup cols={2}>
  <Card
    title="API 指南"
    icon="book"
    href="/docs/zh-CN/build-with-claude/skills-guide"
  >
    使用 Claude API 的 Skills
  </Card>
  <Card
    title="创建自定义 Skills"
    icon="code"
    href="/docs/zh-CN/api/skills/create-skill"
  >
    上传您自己的 Skills 用于专门任务
  </Card>
  <Card
    title="创作指南"
    icon="edit"
    href="/docs/zh-CN/agents-and-tools/agent-skills/best-practices"
  >
    学习编写有效 Skills 的最佳实践
  </Card>
  <Card
    title="在 Claude Code 中使用 Skills"
    icon="terminal"
    href="https://code.claude.com/docs/skills"
  >
    了解 Claude Code 中的 Skills
  </Card>
  <Card
    title="在 Agent SDK 中使用 Skills"
    icon="cube"
    href="/docs/zh-CN/agent-sdk/skills"
  >
    在 TypeScript 和 Python 中以编程方式使用 Skills
  </Card>
  <Card
    title="Agent Skills Cookbook"
    icon="book"
    href="https://github.com/anthropics/anthropic-cookbook/blob/main/skills/README.md"
  >
    探索示例 Skills 和实现模式
  </Card>
</CardGroup>

# 技能创作最佳实践

学习如何编写有效的技能，使 Claude 能够发现和成功使用。

---

好的技能应该简洁、结构良好且经过真实使用测试。本指南提供实用的创作决策，帮助您编写 Claude 能够有效发现和使用的技能。

有关技能工作原理的概念背景，请参阅[技能概述](/docs/zh-CN/agents-and-tools/agent-skills/overview)。

## 核心原则

### 简洁是关键

[上下文窗口](/docs/zh-CN/build-with-claude/context-windows)是一种公共资源。您的技能与 Claude 需要了解的所有其他内容共享上下文窗口，包括：
- 系统提示
- 对话历史
- 其他技能的元数据
- 您的实际请求

技能中的每个令牌都没有直接成本。启动时，只有所有技能的元数据（名称和描述）被预加载。Claude 仅在技能变得相关时才读取 SKILL.md，并根据需要读取其他文件。但是，在 SKILL.md 中保持简洁仍然很重要：一旦 Claude 加载它，每个令牌都会与对话历史和其他上下文竞争。

**默认假设**：Claude 已经非常聪明

只添加 Claude 没有的上下文。质疑每一条信息：
- "Claude 真的需要这个解释吗？"
- "我能假设 Claude 知道这个吗？"
- "这段落值得它的令牌成本吗？"

**好的例子：简洁**（大约 50 个令牌）：
````markdown
## 提取 PDF 文本

使用 pdfplumber 进行文本提取：

```python
import pdfplumber

with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
````

**不好的例子：过于冗长**（大约 150 个令牌）：
```markdown
## 提取 PDF 文本

PDF（便携式文档格式）文件是一种常见的文件格式，包含
文本、图像和其他内容。要从 PDF 中提取文本，您需要
使用一个库。有许多库可用于 PDF 处理，但我们
建议使用 pdfplumber，因为它易于使用且能处理大多数情况。
首先，您需要使用 pip 安装它。然后您可以使用下面的代码...
```

简洁版本假设 Claude 知道什么是 PDF 以及库如何工作。

### 设置适当的自由度

将具体程度与任务的脆弱性和可变性相匹配。

**高自由度**（基于文本的说明）：

使用场景：
- 多种方法都有效
- 决策取决于上下文
- 启发式方法指导方法

示例：
```markdown
## 代码审查流程

1. 分析代码结构和组织
2. 检查潜在的错误或边界情况
3. 建议改进可读性和可维护性
4. 验证是否遵守项目约定
```

**中等自由度**（伪代码或带参数的脚本）：

使用场景：
- 存在首选模式
- 某些变化是可以接受的
- 配置影响行为

示例：
````markdown
## 生成报告

使用此模板并根据需要自定义：

```python
def generate_report(data, format="markdown", include_charts=True):
    # 处理数据
    # 以指定格式生成输出
    # 可选地包含可视化
```
````

**低自由度**（特定脚本，很少或没有参数）：

使用场景：
- 操作脆弱且容易出错
- 一致性至关重要
- 必须遵循特定的序列

示例：
````markdown
## 数据库迁移

运行完全相同的脚本：

```bash
python scripts/migrate.py --verify --backup
```

不要修改命令或添加其他标志。
````

**类比**：将 Claude 视为探索路径的机器人：
- **两侧都是悬崖的狭窄桥**：只有一种安全的前进方式。提供具体的护栏和精确的说明（低自由度）。示例：必须按精确顺序运行的数据库迁移。
- **没有危险的开放田野**：许多路径都能成功。给出一般方向并相信 Claude 会找到最佳路线（高自由度）。示例：上下文决定最佳方法的代码审查。

### 使用您计划使用的所有模型进行测试

技能作为模型的附加功能，因此有效性取决于底层模型。使用您计划使用的所有模型测试您的技能。

**按模型的测试考虑**：
- **Claude Haiku**（快速、经济）：技能是否提供了足够的指导？
- **Claude Sonnet**（平衡）：技能是否清晰高效？
- **Claude Opus**（强大的推理）：技能是否避免过度解释？

对 Opus 完美有效的东西可能需要为 Haiku 提供更多细节。如果您计划在多个模型中使用您的技能，请针对所有模型都能很好地工作的说明。

## 技能结构

<Note>
**YAML 前置事项**：SKILL.md 前置事项需要两个字段：

`name`：
- 最多 64 个字符
- 只能包含小写字母、数字和连字符
- 不能包含 XML 标签
- 不能包含保留字："anthropic"、"claude"

`description`：
- 必须非空
- 最多 1024 个字符
- 不能包含 XML 标签
- 应描述技能的功能和使用时机

有关完整的技能结构详情，请参阅[技能概述](/docs/zh-CN/agents-and-tools/agent-skills/overview#skill-structure)。
</Note>

### 命名约定

使用一致的命名模式使技能更容易引用和讨论。我们建议对技能名称使用**动名词形式**（动词 + -ing），因为这清楚地描述了技能提供的活动或能力。

请记住，`name` 字段必须仅使用小写字母、数字和连字符。

**好的命名示例（动名词形式）**：
- `processing-pdfs`
- `analyzing-spreadsheets`
- `managing-databases`
- `testing-code`
- `writing-documentation`

**可接受的替代方案**：
- 名词短语：`pdf-processing`、`spreadsheet-analysis`
- 面向行动：`process-pdfs`、`analyze-spreadsheets`

**避免**：
- 模糊的名称：`helper`、`utils`、`tools`
- 过于通用：`documents`、`data`、`files`
- 保留字：`anthropic-helper`、`claude-tools`
- 技能集合中的不一致模式

一致的命名使以下操作更容易：
- 在文档和对话中引用技能
- 一目了然地理解技能的功能
- 组织和搜索多个技能
- 维护专业、统一的技能库

### 编写有效的描述

`description` 字段启用技能发现，应包括技能的功能和使用时机。

<Warning>
**始终用第三人称编写**。描述被注入到系统提示中，不一致的视角可能会导致发现问题。

- **好的**："处理 Excel 文件并生成报告"
- **避免**："我可以帮助您处理 Excel 文件"
- **避免**："您可以使用此功能处理 Excel 文件"
</Warning>

**具体并包含关键术语**。包括技能的功能和使用它的具体触发器/上下文。

每个技能恰好有一个描述字段。描述对于技能选择至关重要：Claude 使用它从可能的 100+ 个可用技能中选择正确的技能。您的描述必须提供足够的细节，以便 Claude 知道何时选择此技能，而 SKILL.md 的其余部分提供实现细节。

有效的示例：

**PDF 处理技能**：
```yaml
description: 从 PDF 文件中提取文本和表格、填充表单、合并文档。在处理 PDF 文件或用户提及 PDF、表单或文档提取时使用。
```

**Excel 分析技能**：
```yaml
description: 分析 Excel 电子表格、创建数据透视表、生成图表。在分析 Excel 文件、电子表格、表格数据或 .xlsx 文件时使用。
```

**Git 提交助手技能**：
```yaml
description: 通过分析 git 差异生成描述性提交消息。当用户要求帮助编写提交消息或审查暂存更改时使用。
```

避免模糊的描述，如：

```yaml
description: 帮助处理文档
```
```yaml
description: 处理数据
```
```yaml
description: 对文件进行各种操作
```

### 渐进式披露模式

SKILL.md 作为概述，指向 Claude 根据需要查看的详细材料，就像入职指南中的目录一样。有关渐进式披露如何工作的解释，请参阅概述中的[技能如何工作](/docs/zh-CN/agents-and-tools/agent-skills/overview#how-skills-work)。

**实用指导**：
- 保持 SKILL.md 正文在 500 行以下以获得最佳性能
- 接近此限制时将内容拆分为单独的文件
- 使用下面的模式有效地组织说明、代码和资源

#### 视觉概览：从简单到复杂

基本技能仅包含一个 SKILL.md 文件，其中包含元数据和说明：

![显示 YAML 前置事项和 markdown 正文的简单 SKILL.md 文件](/docs/images/agent-skills-simple-file.png)

随着您的技能增长，您可以捆绑 Claude 仅在需要时加载的其他内容：

![捆绑其他参考文件，如 reference.md 和 forms.md。](/docs/images/agent-skills-bundling-content.png)

完整的技能目录结构可能如下所示：

```
pdf/
├── SKILL.md              # 主要说明（触发时加载）
├── FORMS.md              # 表单填充指南（根据需要加载）
├── reference.md          # API 参考（根据需要加载）
├── examples.md           # 使用示例（根据需要加载）
└── scripts/
    ├── analyze_form.py   # 实用脚本（执行，不加载）
    ├── fill_form.py      # 表单填充脚本
    └── validate.py       # 验证脚本
```

#### 模式 1：高级指南与参考

````markdown
---
name: pdf-processing
description: 从 PDF 文件中提取文本和表格、填充表单、合并文档。在处理 PDF 文件或用户提及 PDF、表单或文档提取时使用。
---

# PDF 处理

## 快速开始

使用 pdfplumber 提取文本：
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

## 高级功能

**表单填充**：参阅 [FORMS.md](FORMS.md) 获取完整指南
**API 参考**：参阅 [REFERENCE.md](REFERENCE.md) 获取所有方法
**示例**：参阅 [EXAMPLES.md](EXAMPLES.md) 获取常见模式
````

Claude 仅在需要时加载 FORMS.md、REFERENCE.md 或 EXAMPLES.md。

#### 模式 2：特定领域组织

对于具有多个领域的技能，按领域组织内容以避免加载无关的上下文。当用户询问销售指标时，Claude 只需要读取与销售相关的架构，而不是财务或营销数据。这保持令牌使用低且上下文集中。

```
bigquery-skill/
├── SKILL.md (概述和导航)
└── reference/
    ├── finance.md (收入、计费指标)
    ├── sales.md (机会、管道)
    ├── product.md (API 使用、功能)
    └── marketing.md (活动、归因)
```

````markdown SKILL.md
# BigQuery 数据分析

## 可用数据集

**财务**：收入、ARR、计费 → 参阅 [reference/finance.md](reference/finance.md)
**销售**：机会、管道、账户 → 参阅 [reference/sales.md](reference/sales.md)
**产品**：API 使用、功能、采用 → 参阅 [reference/product.md](reference/product.md)
**营销**：活动、归因、电子邮件 → 参阅 [reference/marketing.md](reference/marketing.md)

## 快速搜索

使用 grep 查找特定指标：

```bash
grep -i "revenue" reference/finance.md
grep -i "pipeline" reference/sales.md
grep -i "api usage" reference/product.md
```
````

#### 模式 3：条件详情

显示基本内容，链接到高级内容：

```markdown
# DOCX 处理

## 创建文档

使用 docx-js 创建新文档。参阅 [DOCX-JS.md](DOCX-JS.md)。

## 编辑文档

对于简单编辑，直接修改 XML。

**对于跟踪更改**：参阅 [REDLINING.md](REDLINING.md)
**对于 OOXML 详情**：参阅 [OOXML.md](OOXML.md)
```

Claude 仅在用户需要这些功能时读取 REDLINING.md 或 OOXML.md。

### 避免深层嵌套引用

当从其他引用文件引用文件时，Claude 可能会部分读取文件。遇到嵌套引用时，Claude 可能会使用 `head -100` 等命令预览内容，而不是读取整个文件，导致信息不完整。

**保持引用距离 SKILL.md 一级**。所有参考文件应直接从 SKILL.md 链接，以确保 Claude 在需要时读取完整文件。

**不好的例子：太深**：
```markdown
# SKILL.md
参阅 [advanced.md](advanced.md)...

# advanced.md
参阅 [details.md](details.md)...

# details.md
这是实际信息...
```

**好的例子：一级深**：
```markdown
# SKILL.md

**基本使用**：[SKILL.md 中的说明]
**高级功能**：参阅 [advanced.md](advanced.md)
**API 参考**：参阅 [reference.md](reference.md)
**示例**：参阅 [examples.md](examples.md)
```

### 使用目录结构化较长的参考文件

对于超过 100 行的参考文件，在顶部包含目录。这确保 Claude 即使在部分读取时也能看到可用信息的完整范围。

**示例**：
```markdown
# API 参考

## 内容
- 身份验证和设置
- 核心方法（创建、读取、更新、删除）
- 高级功能（批量操作、webhooks）
- 错误处理模式
- 代码示例

## 身份验证和设置
...

## 核心方法
...
```

Claude 可以根据需要读取完整文件或跳转到特定部分。

有关此基于文件系统的架构如何启用渐进式披露的详情，请参阅下面"高级"部分中的[运行时环境](#runtime-environment)部分。

## 工作流和反馈循环

### 对复杂任务使用工作流

将复杂操作分解为清晰的顺序步骤。对于特别复杂的工作流，提供一个清单，Claude 可以将其复制到其响应中并在进行时检查。

**示例 1：研究综合工作流**（适用于没有代码的技能）：

````markdown
## 研究综合工作流

复制此清单并跟踪您的进度：

```
研究进度：
- [ ] 步骤 1：阅读所有源文档
- [ ] 步骤 2：识别关键主题
- [ ] 步骤 3：交叉参考声明
- [ ] 步骤 4：创建结构化摘要
- [ ] 步骤 5：验证引用
```

**步骤 1：阅读所有源文档**

查看 `sources/` 目录中的每个文档。记下主要论点和支持证据。

**步骤 2：识别关键主题**

寻找跨源的模式。哪些主题重复出现？源在哪里一致或不一致？

**步骤 3：交叉参考声明**

对于每个主要声明，验证它出现在源材料中。记下哪个源支持每个点。

**步骤 4：创建结构化摘要**

按主题组织发现。包括：
- 主要声明
- 来自源的支持证据
- 相互矛盾的观点（如果有）

**步骤 5：验证引用**

检查每个声明是否引用了正确的源文档。如果引用不完整，返回步骤 3。
````

此示例展示了工作流如何应用于不需要代码的分析任务。清单模式适用于任何复杂的多步骤流程。

**示例 2：PDF 表单填充工作流**（适用于有代码的技能）：

````markdown
## PDF 表单填充工作流

复制此清单并在完成项目时检查：

```
任务进度：
- [ ] 步骤 1：分析表单（运行 analyze_form.py）
- [ ] 步骤 2：创建字段映射（编辑 fields.json）
- [ ] 步骤 3：验证映射（运行 validate_fields.py）
- [ ] 步骤 4：填充表单（运行 fill_form.py）
- [ ] 步骤 5：验证输出（运行 verify_output.py）
```

**步骤 1：分析表单**

运行：`python scripts/analyze_form.py input.pdf`

这提取表单字段及其位置，保存到 `fields.json`。

**步骤 2：创建字段映射**

编辑 `fields.json` 为每个字段添加值。

**步骤 3：验证映射**

运行：`python scripts/validate_fields.py fields.json`

在继续之前修复任何验证错误。

**步骤 4：填充表单**

运行：`python scripts/fill_form.py input.pdf fields.json output.pdf`

**步骤 5：验证输出**

运行：`python scripts/verify_output.py output.pdf`

如果验证失败，返回步骤 2。
````

清晰的步骤防止 Claude 跳过关键验证。清单帮助 Claude 和您跟踪多步骤工作流的进度。

### 实现反馈循环

**常见模式**：运行验证器 → 修复错误 → 重复

此模式大大提高输出质量。

**示例 1：风格指南合规性**（适用于没有代码的技能）：

```markdown
## 内容审查流程

1. 按照 STYLE_GUIDE.md 中的指南起草您的内容
2. 根据清单审查：
   - 检查术语一致性
   - 验证示例遵循标准格式
   - 确认所有必需部分都存在
3. 如果发现问题：
   - 用特定部分参考记录每个问题
   - 修改内容
   - 再次审查清单
4. 仅当满足所有要求时才继续
5. 完成并保存文档
```

这展示了使用参考文档而不是脚本的验证循环模式。"验证器"是 STYLE_GUIDE.md，Claude 通过读取和比较来执行检查。

**示例 2：文档编辑流程**（适用于有代码的技能）：

```markdown
## 文档编辑流程

1. 对 `word/document.xml` 进行编辑
2. **立即验证**：`python ooxml/scripts/validate.py unpacked_dir/`
3. 如果验证失败：
   - 仔细查看错误消息
   - 修复 XML 中的问题
   - 再次运行验证
4. **仅在验证通过时继续**
5. 重建：`python ooxml/scripts/pack.py unpacked_dir/ output.docx`
6. 测试输出文档
```

验证循环可以及早捕获错误。

## 内容指南

### 避免时间敏感信息

不要包含会过时的信息：

**不好的例子：时间敏感**（会变成错误）：
```markdown
如果您在 2025 年 8 月之前执行此操作，请使用旧 API。
2025 年 8 月之后，使用新 API。
```

**好的例子**（使用"旧模式"部分）：
```markdown
## 当前方法

使用 v2 API 端点：`api.example.com/v2/messages`

## 旧模式

<details>
<summary>旧版 v1 API（已弃用 2025-08）</summary>

v1 API 使用：`api.example.com/v1/messages`

此端点不再受支持。
</details>
```

旧模式部分提供历史背景，而不会使主要内容混乱。

### 使用一致的术语

选择一个术语并在整个技能中使用它：

**好的 - 一致**：
- 始终"API 端点"
- 始终"字段"
- 始终"提取"

**不好的 - 不一致**：
- 混合"API 端点"、"URL"、"API 路由"、"路径"
- 混合"字段"、"框"、"元素"、"控件"
- 混合"提取"、"拉取"、"获取"、"检索"

一致性帮助 Claude 理解和遵循说明。

## 常见模式

### 模板模式

为输出格式提供模板。将严格程度与您的需求相匹配。

**对于严格要求**（如 API 响应或数据格式）：

````markdown
## 报告结构

始终使用此精确的模板结构：

```markdown
# [分析标题]

## 执行摘要
[关键发现的一段概述]

## 关键发现
- 带有支持数据的发现 1
- 带有支持数据的发现 2
- 带有支持数据的发现 3

## 建议
1. 具体可行的建议
2. 具体可行的建议
```
````

**对于灵活指导**（当适应有用时）：

````markdown
## 报告结构

这是一个合理的默认格式，但根据分析使用您的最佳判断：

```markdown
# [分析标题]

## 执行摘要
[概述]

## 关键发现
[根据您发现的内容调整部分]

## 建议
[根据具体背景定制]
```

根据特定分析类型根据需要调整部分。
````

### 示例模式

对于输出质量取决于看到示例的技能，提供输入/输出对，就像在常规提示中一样：

````markdown
## 提交消息格式

按照这些示例生成提交消息：

**示例 1：**
输入：使用 JWT 令牌添加用户身份验证
输出：
```
feat(auth): 实现基于 JWT 的身份验证

添加登录端点和令牌验证中间件
```

**示例 2：**
输入：修复日期在报告中显示不正确的错误
输出：
```
fix(reports): 修正时区转换中的日期格式

在报告生成中一致使用 UTC 时间戳
```

**示例 3：**
输入：更新依赖项并重构错误处理
输出：
```
chore: 更新依赖项并重构错误处理

- 将 lodash 升级到 4.17.21
- 跨端点标准化错误响应格式
```

遵循此风格：type(scope): 简短描述，然后详细说明。
````

示例帮助 Claude 比单独的描述更清楚地理解所需的风格和细节程度。

### 条件工作流模式

通过决策点指导 Claude：

```markdown
## 文档修改工作流

1. 确定修改类型：

   **创建新内容？** → 遵循下面的"创建工作流"
   **编辑现有内容？** → 遵循下面的"编辑工作流"

2. 创建工作流：
   - 使用 docx-js 库
   - 从头开始构建文档
   - 导出为 .docx 格式

3. 编辑工作流：
   - 解包现有文档
   - 直接修改 XML
   - 每次更改后验证
   - 完成时重新打包
```

<Tip>
如果工作流变得很大或复杂，有许多步骤，考虑将它们推送到单独的文件中，并告诉 Claude 根据任务读取适当的文件。
</Tip>

## 评估和迭代

### 首先构建评估

**在编写大量文档之前创建评估。** 这确保您的技能解决真实问题，而不是记录想象的问题。

**评估驱动的开发**：
1. **识别差距**：在没有技能的情况下对代表性任务运行 Claude。记录具体的失败或缺失的上下文
2. **创建评估**：构建三个场景来测试这些差距
3. **建立基线**：测量没有技能的 Claude 的性能
4. **编写最少说明**：创建足够的内容来解决差距并通过评估
5. **迭代**：执行评估、与基线比较并改进

此方法确保您解决实际问题，而不是预期可能永远不会出现的要求。

**评估结构**：
```json
{
  "skills": ["pdf-processing"],
  "query": "从此 PDF 文件中提取所有文本并将其保存到 output.txt",
  "files": ["test-files/document.pdf"],
  "expected_behavior": [
    "使用适当的 PDF 处理库或命令行工具成功读取 PDF 文件",
    "从文档中的所有页面提取文本内容，不遗漏任何页面",
    "将提取的文本保存到名为 output.txt 的文件中，格式清晰易读"
  ]
}
```

<Note>
此示例演示了具有简单测试标准的数据驱动评估。我们目前不提供运行这些评估的内置方式。用户可以创建自己的评估系统。评估是衡量技能有效性的真实来源。
</Note>

### 与 Claude 一起迭代开发技能

最有效的技能开发流程涉及 Claude 本身。与一个 Claude 实例（"Claude A"）合作创建将由其他实例（"Claude B"）使用的技能。Claude A 帮助您设计和改进说明，而 Claude B 在真实任务中测试它们。这之所以有效，是因为 Claude 模型既理解如何编写有效的代理说明，也理解代理需要什么信息。

**创建新技能**：

1. **在没有技能的情况下完成任务**：与 Claude A 一起使用常规提示来解决问题。在您工作时，您自然会提供上下文、解释偏好并分享程序知识。注意您重复提供的信息。

2. **识别可重用模式**：完成任务后，识别您提供的对类似未来任务有用的上下文。

   **示例**：如果您完成了 BigQuery 分析，您可能提供了表名、字段定义、过滤规则（如"始终排除测试账户"）和常见查询模式。

3. **要求 Claude A 创建技能**："创建一个技能来捕获我们刚刚使用的 BigQuery 分析模式。包括表架构、命名约定和关于过滤测试账户的规则。"

   <Tip>
   Claude 模型本身理解技能格式和结构。您不需要特殊的系统提示或"编写技能"技能来让 Claude 帮助创建技能。只需要求 Claude 创建技能，它就会生成具有适当前置事项和正文内容的正确结构化 SKILL.md。
   </Tip>

4. **审查简洁性**：检查 Claude A 是否没有添加不必要的解释。问："删除关于赢率意义的解释 - Claude 已经知道这个。"

5. **改进信息架构**：要求 Claude A 更有效地组织内容。例如："组织这个，使表架构在单独的参考文件中。我们稍后可能会添加更多表。"

6. **在类似任务上测试**：使用技能与 Claude B（一个加载了技能的新实例）进行相关用例。观察 Claude B 是否找到正确的信息、正确应用规则并成功处理任务。

7. **根据观察迭代**：如果 Claude B 遇到困难或遗漏了什么，返回 Claude A 并提供具体信息："当 Claude 使用此技能时，它忘记了为 Q4 按日期过滤。我们应该添加关于日期过滤模式的部分吗？"

**迭代现有技能**：

当改进技能时，相同的分层模式继续。您在以下之间交替：
- **与 Claude A 合作**（帮助改进技能的专家）
- **与 Claude B 测试**（使用技能执行真实工作的代理）
- **观察 Claude B 的行为**并将见解带回 Claude A

1. **在真实工作流中使用技能**：给 Claude B（加载了技能）实际任务，而不是测试场景

2. **观察 Claude B 的行为**：注意它在哪里遇到困难、成功或做出意外选择

   **示例观察**："当我要求 Claude B 生成区域销售报告时，它编写了查询但忘记了过滤测试账户，即使技能提到了此规则。"

3. **返回 Claude A 进行改进**：分享当前的 SKILL.md 并描述您观察到的内容。问："我注意到 Claude B 在要求区域报告时忘记了过滤测试账户。技能提到了过滤，但也许还不够突出？"

4. **审查 Claude A 的建议**：Claude A 可能建议重新组织以使规则更突出、使用更强的语言如"必须过滤"而不是"始终过滤"，或重构工作流部分。

5. **应用并测试更改**：使用 Claude A 的改进更新技能，然后在类似请求上再次与 Claude B 测试

6. **根据使用情况重复**：当您遇到新场景时继续观察-改进-测试循环。每次迭代都根据真实代理行为而不是假设改进技能。

**收集团队反馈**：

1. 与队友分享技能并观察他们的使用
2. 问："技能在预期时激活吗？说明清楚吗？缺少什么？"
3. 合并反馈以解决您自己使用模式中的盲点

**为什么此方法有效**：Claude A 理解代理需求，您提供领域专业知识，Claude B 通过真实使用揭示差距，迭代改进根据观察到的行为而不是假设改进技能。

### 观察 Claude 如何导航技能

当您迭代技能时，注意 Claude 实际上如何在实践中使用它们。观察：

- **意外的探索路径**：Claude 是否以您没有预期的顺序读取文件？这可能表明您的结构不如您认为的那样直观
- **错过的连接**：Claude 是否未能遵循对重要文件的引用？您的链接可能需要更明确或突出
- **对某些部分的过度依赖**：如果 Claude 反复读取同一文件，考虑该内容是否应该在主 SKILL.md 中
- **忽略的内容**：如果 Claude 从不访问捆绑文件，它可能是不必要的或在主说明中信号不良

根据这些观察而不是假设进行迭代。您的技能元数据中的"name"和"description"特别关键。Claude 在决定是否响应当前任务触发技能时使用这些。确保它们清楚地描述技能的功能和使用时机。

## 要避免的反模式

### 避免 Windows 风格的路径

始终使用正斜杠在文件路径中，即使在 Windows 上：

- ✓ **好的**：`scripts/helper.py`、`reference/guide.md`
- ✗ **避免**：`scripts\helper.py`、`reference\guide.md`

Unix 风格的路径在所有平台上都有效，而 Windows 风格的路径在 Unix 系统上会导致错误。

### 避免提供太多选项

除非必要，否则不要呈现多种方法：

````markdown
**不好的例子：太多选择**（令人困惑）：
"您可以使用 pypdf、或 pdfplumber、或 PyMuPDF、或 pdf2image、或..."

**好的例子：提供默认值**（带有逃生舱口）：
"使用 pdfplumber 进行文本提取：
```python
import pdfplumber
```

对于需要 OCR 的扫描 PDF，改用 pdf2image 与 pytesseract。"
````

## 高级：带有可执行代码的技能

下面的部分重点关注包含可执行脚本的技能。如果您的技能仅使用 markdown 说明，请跳到[有效技能清单](#checklist-for-effective-skills)。

### 解决，不要推卸

编写技能脚本时，处理错误条件而不是推卸给 Claude。

**好的例子：明确处理错误**：
```python
def process_file(path):
    """处理文件，如果不存在则创建它。"""
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        # 创建具有默认内容的文件而不是失败
        print(f"文件 {path} 未找到，创建默认值")
        with open(path, 'w') as f:
            f.write('')
        return ''
    except PermissionError:
        # 提供替代方案而不是失败
        print(f"无法访问 {path}，使用默认值")
        return ''
```

**不好的例子：推卸给 Claude**：
```python
def process_file(path):
    # 只是失败并让 Claude 弄清楚
    return open(path).read()
```

配置参数也应该被证明和记录，以避免"巫毒常数"（Ousterhout 定律）。如果您不知道正确的值，Claude 如何确定它？

**好的例子：自文档化**：
```python
# HTTP 请求通常在 30 秒内完成
# 更长的超时考虑了慢速连接
REQUEST_TIMEOUT = 30

# 三次重试平衡可靠性与速度
# 大多数间歇性故障在第二次重试时解决
MAX_RETRIES = 3
```

**不好的例子：魔法数字**：
```python
TIMEOUT = 47  # 为什么是 47？
RETRIES = 5   # 为什么是 5？
```

### 提供实用脚本

即使 Claude 可以编写脚本，预制脚本也提供优势：

**实用脚本的优势**：
- 比生成的代码更可靠
- 节省令牌（无需在上下文中包含代码）
- 节省时间（无需代码生成）
- 确保跨使用的一致性

![将可执行脚本与说明文件捆绑在一起](/docs/images/agent-skills-executable-scripts.png)

上面的图表显示了可执行脚本如何与说明文件一起工作。说明文件（forms.md）引用脚本，Claude 可以执行它而无需将其内容加载到上下文中。

**重要区别**：在您的说明中明确说明 Claude 是否应该：
- **执行脚本**（最常见）："运行 `analyze_form.py` 来提取字段"
- **作为参考读取**（对于复杂逻辑）："参阅 `analyze_form.py` 了解字段提取算法"

对于大多数实用脚本，执行是首选，因为它更可靠和高效。有关脚本执行如何工作的详情，请参阅下面的[运行时环境](#runtime-environment)部分。

**示例**：
````markdown
## 实用脚本

**analyze_form.py**：从 PDF 中提取所有表单字段

```bash
python scripts/analyze_form.py input.pdf > fields.json
```

输出格式：
```json
{
  "field_name": {"type": "text", "x": 100, "y": 200},
  "signature": {"type": "sig", "x": 150, "y": 500}
}
```

**validate_boxes.py**：检查重叠的边界框

```bash
python scripts/validate_boxes.py fields.json
# 返回："OK"或列出冲突
```

**fill_form.py**：将字段值应用于 PDF

```bash
python scripts/fill_form.py input.pdf fields.json output.pdf
```
````

### 使用视觉分析

当输入可以呈现为图像时，让 Claude 分析它们：

````markdown
## 表单布局分析

1. 将 PDF 转换为图像：
   ```bash
   python scripts/pdf_to_images.py form.pdf
   ```

2. 分析每个页面图像以识别表单字段
3. Claude 可以在视觉上看到字段位置和类型
````

<Note>
在此示例中，您需要编写 `pdf_to_images.py` 脚本。
</Note>

Claude 的视觉能力帮助理解布局和结构。

### 创建可验证的中间输出

当 Claude 执行复杂的开放式任务时，它可能会犯错误。"计划-验证-执行"模式通过让 Claude 首先以结构化格式创建计划，然后在执行前使用脚本验证该计划来及早捕获错误。

**示例**：想象要求 Claude 根据电子表格更新 PDF 中的 50 个表单字段。没有验证，Claude 可能会引用不存在的字段、创建冲突的值、遗漏必需字段或错误地应用更新。

**解决方案**：使用上面显示的工作流模式（PDF 表单填充），但添加一个中间 `changes.json` 文件，在应用更改前进行验证。工作流变成：分析 → **创建计划文件** → **验证计划** → 执行 → 验证。

**为什么此模式有效**：
- **及早捕获错误**：验证在更改应用前发现问题
- **机器可验证**：脚本提供客观验证
- **可逆计划**：Claude 可以迭代计划而不接触原件
- **清晰调试**：错误消息指向特定问题

**何时使用**：批量操作、破坏性更改、复杂验证规则、高风险操作。

**实现提示**：使用详细的验证脚本和特定的错误消息，如"字段 'signature_date' 未找到。可用字段：customer_name、order_total、signature_date_signed"来帮助 Claude 修复问题。

### 打包依赖项

技能在代码执行环境中运行，具有特定于平台的限制：

- **claude.ai**：可以从 npm 和 PyPI 安装包并从 GitHub 存储库拉取
- **Anthropic API**：没有网络访问权限，没有运行时包安装

在您的 SKILL.md 中列出所需的包，并验证它们在[代码执行工具文档](/docs/zh-CN/agents-and-tools/tool-use/code-execution-tool)中可用。

### 运行时环境

技能在具有文件系统访问、bash 命令和代码执行能力的代码执行环境中运行。有关此架构的概念解释，请参阅概述中的[技能架构](/docs/zh-CN/agents-and-tools/agent-skills/overview#the-skills-architecture)。

**这如何影响您的创作**：

**Claude 如何访问技能**：

1. **元数据预加载**：启动时，所有技能 YAML 前置事项中的名称和描述被加载到系统提示中
2. **按需读取文件**：Claude 在需要时使用 bash 读取工具从文件系统访问 SKILL.md 和其他文件
3. **高效执行脚本**：实用脚本可以通过 bash 执行，而无需将其完整内容加载到上下文中。只有脚本的输出消耗令牌
4. **大文件无上下文惩罚**：参考文件、数据或文档在实际读取前不消耗上下文令牌

- **文件路径很重要**：Claude 像文件系统一样导航您的技能目录。使用正斜杠（`reference/guide.md`），而不是反斜杠
- **描述性地命名文件**：使用指示内容的名称：`form_validation_rules.md`，而不是 `doc2.md`
- **为发现组织**：按域或功能组织目录
  - 好的：`reference/finance.md`、`reference/sales.md`
  - 不好的：`docs/file1.md`、`docs/file2.md`
- **捆绑综合资源**：包括完整的 API 文档、广泛的示例、大型数据集；在访问前没有上下文惩罚
- **对确定性操作优先使用脚本**：编写 `validate_form.py` 而不是要求 Claude 生成验证代码
- **明确执行意图**：
  - "运行 `analyze_form.py` 来提取字段"（执行）
  - "参阅 `analyze_form.py` 了解提取算法"（作为参考读取）
- **测试文件访问模式**：通过使用真实请求测试来验证 Claude 可以导航您的目录结构

**示例**：

```
bigquery-skill/
├── SKILL.md (概述，指向参考文件)
└── reference/
    ├── finance.md (收入指标)
    ├── sales.md (管道数据)
    └── product.md (使用分析)
```

当用户询问收入时，Claude 读取 SKILL.md，看到对 `reference/finance.md` 的参考，并调用 bash 来仅读取该文件。sales.md 和 product.md 文件保留在文件系统上，在需要前消耗零上下文令牌。这个基于文件系统的模型是启用渐进式披露的原因。Claude 可以导航并有选择地加载每个任务所需的内容。

有关技术架构的完整详情，请参阅技能概述中的[技能如何工作](/docs/zh-CN/agents-and-tools/agent-skills/overview#how-skills-work)。

### MCP 工具参考

如果您的技能使用 MCP（模型上下文协议）工具，始终使用完全限定的工具名称以避免"找不到工具"错误。

**格式**：`ServerName:tool_name`

**示例**：
```markdown
使用 BigQuery:bigquery_schema 工具检索表架构。
使用 GitHub:create_issue 工具创建问题。
```

其中：
- `BigQuery` 和 `GitHub` 是 MCP 服务器名称
- `bigquery_schema` 和 `create_issue` 是这些服务器中的工具名称

没有服务器前缀，Claude 可能无法定位工具，特别是当有多个 MCP 服务器可用时。

### 避免假设工具已安装

不要假设包可用：

````markdown
**不好的例子：假设安装**：
"使用 pdf 库来处理文件。"

**好的例子：明确关于依赖项**：
"安装所需的包：`pip install pypdf`

然后使用它：
```python
from pypdf import PdfReader
reader = PdfReader("file.pdf")
```"
````

## 技术说明

### YAML 前置事项要求

SKILL.md 前置事项需要 `name` 和 `description` 字段，具有特定的验证规则：
- `name`：最多 64 个字符，仅小写字母/数字/连字符，无 XML 标签，无保留字
- `description`：最多 1024 个字符，非空，无 XML 标签

有关完整的结构详情，请参阅[技能概述](/docs/zh-CN/agents-and-tools/agent-skills/overview#skill-structure)。

### 令牌预算

保持 SKILL.md 正文在 500 行以下以获得最佳性能。如果您的内容超过此限制，使用前面描述的渐进式披露模式将其拆分为单独的文件。有关架构详情，请参阅[技能概述](/docs/zh-CN/agents-and-tools/agent-skills/overview#how-skills-work)。

## 有效技能清单

在分享技能之前，验证：

### 核心质量
- [ ] 描述具体并包含关键术语
- [ ] 描述包括技能的功能和使用时机
- [ ] SKILL.md 正文在 500 行以下
- [ ] 其他详情在单独的文件中（如果需要）
- [ ] 没有时间敏感信息（或在"旧模式"部分中）
- [ ] 整个技能中术语一致
- [ ] 示例具体，不抽象
- [ ] 文件引用一级深
- [ ] 适当使用渐进式披露
- [ ] 工作流有清晰的步骤

### 代码和脚本
- [ ] 脚本解决问题而不是推卸给 Claude
- [ ] 错误处理明确且有帮助
- [ ] 没有"巫毒常数"（所有值都有理由）
- [ ] 所需的包在说明中列出并验证为可用
- [ ] 脚本有清晰的文档
- [ ] 没有 Windows 风格的路径（所有正斜杠）
- [ ] 关键操作的验证/验证步骤
- [ ] 包含质量关键任务的反馈循环

### 测试
- [ ] 至少创建了三个评估
- [ ] 使用 Haiku、Sonnet 和 Opus 进行了测试
- [ ] 使用真实使用场景进行了测试
- [ ] 合并了团队反馈（如果适用）

## 后续步骤

<CardGroup cols={2}>
  <Card
    title="开始使用代理技能"
    icon="rocket"
    href="/docs/zh-CN/agents-and-tools/agent-skills/quickstart"
  >
    创建您的第一个技能
  </Card>
  <Card
    title="在 Claude Code 中使用技能"
    icon="terminal"
    href="https://code.claude.com/docs/skills"
  >
    在 Claude Code 中创建和管理技能
  </Card>
  <Card
    title="在代理 SDK 中使用技能"
    icon="cube"
    href="/docs/zh-CN/agent-sdk/skills"
  >
    在 TypeScript 和 Python 中以编程方式使用技能
  </Card>
  <Card
    title="使用 API 使用技能"
    icon="code"
    href="/docs/zh-CN/build-with-claude/skills-guide"
  >
    以编程方式上传和使用技能
  </Card>
</CardGroup>

# 通过 API 使用 Agent Skills

了解如何通过 API 使用 Agent Skills 来扩展 Claude 的功能。

---

Agent Skills 通过组织化的指令、脚本和资源文件夹来扩展 Claude 的功能。本指南展示了如何在 Claude API 中使用预构建和自定义 Skills。

<Note>
有关完整的 API 参考（包括请求/响应架构和所有参数），请参阅：
- [Skill 管理 API 参考](/docs/zh-CN/api/skills/list-skills) - Skills 的 CRUD 操作
- [Skill 版本 API 参考](/docs/zh-CN/api/skills/list-skill-versions) - 版本管理
</Note>

## 快速链接

<CardGroup cols={2}>
  <Card
    title="开始使用 Agent Skills"
    icon="rocket"
    href="/docs/zh-CN/agents-and-tools/agent-skills/quickstart"
  >
    创建您的第一个 Skill
  </Card>
  <Card
    title="创建自定义 Skills"
    icon="hammer"
    href="/docs/zh-CN/agents-and-tools/agent-skills/best-practices"
  >
    编写 Skills 的最佳实践
  </Card>
</CardGroup>

## 概述

<Note>
有关 Agent Skills 的架构和实际应用的深入探讨，请阅读我们的工程博客：[为真实世界的代理配备 Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)。
</Note>

Skills 通过代码执行工具与 Messages API 集成。无论使用由 Anthropic 管理的预构建 Skills 还是您上传的自定义 Skills，集成形状都是相同的——两者都需要代码执行并使用相同的 `container` 结构。

### 使用 Skills

无论来源如何，Skills 在 Messages API 中的集成方式都是相同的。您在 `container` 参数中指定 Skills，包括 `skill_id`、`type` 和可选的 `version`，它们在代码执行环境中执行。

**您可以从两个来源使用 Skills：**

| 方面 | Anthropic Skills | 自定义 Skills |
|---|---|---|
| **Type 值** | `anthropic` | `custom` |
| **Skill ID** | 短名称：`pptx`、`xlsx`、`docx`、`pdf` | 生成的：`skill_01AbCdEfGhIjKlMnOpQrStUv` |
| **版本格式** | 基于日期：`20251013` 或 `latest` | 纪元时间戳：`1759178010641129` 或 `latest` |
| **管理** | 由 Anthropic 预构建和维护 | 通过 [Skills API](/docs/zh-CN/api/skills/create-skill) 上传和管理 |
| **可用性** | 对所有用户可用 | 仅限您的工作区 |

两个 Skill 来源都由 [List Skills 端点](/docs/zh-CN/api/skills/list-skills) 返回（使用 `source` 参数进行过滤）。集成形状和执行环境是相同的——唯一的区别是 Skills 的来源和管理方式。

### 前置条件

要使用 Skills，您需要：

1. **Anthropic API 密钥**，来自 [Console](/settings/keys)
2. **Beta 头部**：
   - `code-execution-2025-08-25` - 启用代码执行（Skills 需要）
   - `skills-2025-10-02` - 启用 Skills API
   - `files-api-2025-04-14` - 用于上传/下载文件到/从容器
3. **代码执行工具**在您的请求中启用

---

## 在 Messages 中使用 Skills

### Container 参数

Skills 使用 Messages API 中的 `container` 参数指定。每个请求最多可以包含 8 个 Skills。

结构对于 Anthropic 和自定义 Skills 都是相同的——指定必需的 `type` 和 `skill_id`，并可选择包含 `version` 以固定到特定版本：

<CodeGroup>
```python Python
import anthropic

client = anthropic.Anthropic()

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {
                "type": "anthropic",
                "skill_id": "pptx",
                "version": "latest"
            }
        ]
    },
    messages=[{
        "role": "user",
        "content": "Create a presentation about renewable energy"
    }],
    tools=[{
        "type": "code_execution_20250825",
        "name": "code_execution"
    }]
)
```

```typescript TypeScript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

const response = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [
      {
        type: 'anthropic',
        skill_id: 'pptx',
        version: 'latest'
      }
    ]
  },
  messages: [{
    role: 'user',
    content: 'Create a presentation about renewable energy'
  }],
  tools: [{
    type: 'code_execution_20250825',
    name: 'code_execution'
  }]
});
```

```bash Shell
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "container": {
      "skills": [
        {
          "type": "anthropic",
          "skill_id": "pptx",
          "version": "latest"
        }
      ]
    },
    "messages": [{
      "role": "user",
      "content": "Create a presentation about renewable energy"
    }],
    "tools": [{
      "type": "code_execution_20250825",
      "name": "code_execution"
    }]
  }'
```
</CodeGroup>

### 下载生成的文件

当 Skills 创建文档（Excel、PowerPoint、PDF、Word）时，它们在响应中返回 `file_id` 属性。您必须使用 Files API 来下载这些文件。

**工作原理：**
1. Skills 在代码执行期间创建文件
2. 响应包括每个创建的文件的 `file_id`
3. 使用 Files API 下载实际文件内容
4. 在本地保存或根据需要处理

**示例：创建和下载 Excel 文件**

<CodeGroup>
```python Python
import anthropic

client = anthropic.Anthropic()

# 步骤 1：使用 Skill 创建文件
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    messages=[{
        "role": "user",
        "content": "Create an Excel file with a simple budget spreadsheet"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

# 步骤 2：从响应中提取文件 ID
def extract_file_ids(response):
    file_ids = []
    for item in response.content:
        if item.type == 'bash_code_execution_tool_result':
            content_item = item.content
            if content_item.type == 'bash_code_execution_result':
                for file in content_item.content:
                    if hasattr(file, 'file_id'):
                        file_ids.append(file.file_id)
    return file_ids

# 步骤 3：使用 Files API 下载文件
for file_id in extract_file_ids(response):
    file_metadata = client.beta.files.retrieve_metadata(
        file_id=file_id,
        betas=["files-api-2025-04-14"]
    )
    file_content = client.beta.files.download(
        file_id=file_id,
        betas=["files-api-2025-04-14"]
    )

    # 步骤 4：保存到磁盘
    file_content.write_to_file(file_metadata.filename)
    print(f"Downloaded: {file_metadata.filename}")
```

```typescript TypeScript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

// 步骤 1：使用 Skill 创建文件
const response = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [
      {type: 'anthropic', skill_id: 'xlsx', version: 'latest'}
    ]
  },
  messages: [{
    role: 'user',
    content: 'Create an Excel file with a simple budget spreadsheet'
  }],
  tools: [{type: 'code_execution_20250825', name: 'code_execution'}]
});

// 步骤 2：从响应中提取文件 ID
function extractFileIds(response: any): string[] {
  const fileIds: string[] = [];
  for (const item of response.content) {
    if (item.type === 'bash_code_execution_tool_result') {
      const contentItem = item.content;
      if (contentItem.type === 'bash_code_execution_result') {
        for (const file of contentItem.content) {
          if ('file_id' in file) {
            fileIds.push(file.file_id);
          }
        }
      }
    }
  }
  return fileIds;
}

// 步骤 3：使用 Files API 下载文件
const fs = require('fs');
for (const fileId of extractFileIds(response)) {
  const fileMetadata = await client.beta.files.retrieve_metadata(fileId, {
    betas: ['files-api-2025-04-14']
  });
  const fileContent = await client.beta.files.download(fileId, {
    betas: ['files-api-2025-04-14']
  });

  // 步骤 4：保存到磁盘
  fs.writeFileSync(fileMetadata.filename, Buffer.from(await fileContent.arrayBuffer()));
  console.log(`Downloaded: ${fileMetadata.filename}`);
}
```

```bash Shell
# 步骤 1：使用 Skill 创建文件
RESPONSE=$(curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "container": {
      "skills": [
        {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
      ]
    },
    "messages": [{
      "role": "user",
      "content": "Create an Excel file with a simple budget spreadsheet"
    }],
    "tools": [{
      "type": "code_execution_20250825",
      "name": "code_execution"
    }]
  }')

# 步骤 2：从响应中提取 file_id（使用 jq）
FILE_ID=$(echo "$RESPONSE" | jq -r '.content[] | select(.type=="bash_code_execution_tool_result") | .content | select(.type=="bash_code_execution_result") | .content[] | select(.file_id) | .file_id')

# 步骤 3：从元数据获取文件名
FILENAME=$(curl "https://api.anthropic.com/v1/files/$FILE_ID" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: files-api-2025-04-14" | jq -r '.filename')

# 步骤 4：使用 Files API 下载文件
curl "https://api.anthropic.com/v1/files/$FILE_ID/content" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: files-api-2025-04-14" \
  --output "$FILENAME"

echo "Downloaded: $FILENAME"
```
</CodeGroup>

**其他 Files API 操作：**

<CodeGroup>
```python Python
# 获取文件元数据
file_info = client.beta.files.retrieve_metadata(
    file_id=file_id,
    betas=["files-api-2025-04-14"]
)
print(f"Filename: {file_info.filename}, Size: {file_info.size_bytes} bytes")

# 列出所有文件
files = client.beta.files.list(betas=["files-api-2025-04-14"])
for file in files.data:
    print(f"{file.filename} - {file.created_at}")

# 删除文件
client.beta.files.delete(
    file_id=file_id,
    betas=["files-api-2025-04-14"]
)
```

```typescript TypeScript
// 获取文件元数据
const fileInfo = await client.beta.files.retrieve_metadata(fileId, {
  betas: ['files-api-2025-04-14']
});
console.log(`Filename: ${fileInfo.filename}, Size: ${fileInfo.size_bytes} bytes`);

// 列出所有文件
const files = await client.beta.files.list({
  betas: ['files-api-2025-04-14']
});
for (const file of files.data) {
  console.log(`${file.filename} - ${file.created_at}`);
}

// 删除文件
await client.beta.files.delete(fileId, {
  betas: ['files-api-2025-04-14']
});
```

```bash Shell
# 获取文件元数据
curl "https://api.anthropic.com/v1/files/$FILE_ID" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: files-api-2025-04-14"

# 列出所有文件
curl "https://api.anthropic.com/v1/files" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: files-api-2025-04-14"

# 删除文件
curl -X DELETE "https://api.anthropic.com/v1/files/$FILE_ID" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: files-api-2025-04-14"
```
</CodeGroup>

<Note>
有关 Files API 的完整详情，请参阅 [Files API 文档](/docs/zh-CN/api/files-content)。
</Note>

### 多轮对话

通过指定容器 ID 在多个消息中重用相同的容器：

<CodeGroup>
```python Python
# 第一个请求创建容器
response1 = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    messages=[{"role": "user", "content": "Analyze this sales data"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

# 使用相同的容器继续对话
messages = [
    {"role": "user", "content": "Analyze this sales data"},
    {"role": "assistant", "content": response1.content},
    {"role": "user", "content": "What was the total revenue?"}
]

response2 = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "id": response1.container.id,  # 重用容器
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    messages=messages,
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

```typescript TypeScript
// 第一个请求创建容器
const response1 = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [
      {type: 'anthropic', skill_id: 'xlsx', version: 'latest'}
    ]
  },
  messages: [{role: 'user', content: 'Analyze this sales data'}],
  tools: [{type: 'code_execution_20250825', name: 'code_execution'}]
});

// 使用相同的容器继续对话
const messages = [
  {role: 'user', content: 'Analyze this sales data'},
  {role: 'assistant', content: response1.content},
  {role: 'user', content: 'What was the total revenue?'}
];

const response2 = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    id: response1.container.id,  // 重用容器
    skills: [
      {type: 'anthropic', skill_id: 'xlsx', version: 'latest'}
    ]
  },
  messages,
  tools: [{type: 'code_execution_20250825', name: 'code_execution'}]
});
```
</CodeGroup>

### 长时间运行的操作

Skills 可能执行需要多轮的操作。处理 `pause_turn` 停止原因：

<CodeGroup>
```python Python
messages = [{"role": "user", "content": "Process this large dataset"}]
max_retries = 10

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "custom", "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv", "version": "latest"}
        ]
    },
    messages=messages,
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

# 处理长时间操作的 pause_turn
for i in range(max_retries):
    if response.stop_reason != "pause_turn":
        break

    messages.append({"role": "assistant", "content": response.content})
    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        betas=["code-execution-2025-08-25", "skills-2025-10-02"],
        container={
            "id": response.container.id,
            "skills": [
                {"type": "custom", "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv", "version": "latest"}
            ]
        },
        messages=messages,
        tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
    )
```

```typescript TypeScript
let messages = [{role: 'user' as const, content: 'Process this large dataset'}];
const maxRetries = 10;

let response = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [
      {type: 'custom', skill_id: 'skill_01AbCdEfGhIjKlMnOpQrStUv', version: 'latest'}
    ]
  },
  messages,
  tools: [{type: 'code_execution_20250825', name: 'code_execution'}]
});

// 处理长时间操作的 pause_turn
for (let i = 0; i < maxRetries; i++) {
  if (response.stop_reason !== 'pause_turn') {
    break;
  }

  messages.push({role: 'assistant', content: response.content});
  response = await client.beta.messages.create({
    model: 'claude-sonnet-4-5-20250929',
    max_tokens: 4096,
    betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
    container: {
      id: response.container.id,
      skills: [
        {type: 'custom', skill_id: 'skill_01AbCdEfGhIjKlMnOpQrStUv', version: 'latest'}
      ]
    },
    messages,
    tools: [{type: 'code_execution_20250825', name: 'code_execution'}]
  });
}
```

```bash Shell
# 初始请求
RESPONSE=$(curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "container": {
      "skills": [
        {
          "type": "custom",
          "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv",
          "version": "latest"
        }
      ]
    },
    "messages": [{
      "role": "user",
      "content": "Process this large dataset"
    }],
    "tools": [{
      "type": "code_execution_20250825",
      "name": "code_execution"
    }]
  }')

# 检查 stop_reason 并在循环中处理 pause_turn
STOP_REASON=$(echo "$RESPONSE" | jq -r '.stop_reason')
CONTAINER_ID=$(echo "$RESPONSE" | jq -r '.container.id')

while [ "$STOP_REASON" = "pause_turn" ]; do
  # 使用相同的容器继续
  RESPONSE=$(curl https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
    -H "content-type: application/json" \
    -d "{
      \"model\": \"claude-sonnet-4-5-20250929\",
      \"max_tokens\": 4096,
      \"container\": {
        \"id\": \"$CONTAINER_ID\",
        \"skills\": [{
          \"type\": \"custom\",
          \"skill_id\": \"skill_01AbCdEfGhIjKlMnOpQrStUv\",
          \"version\": \"latest\"
        }]
      },
      \"messages\": [/* include conversation history */],
      \"tools\": [{
        \"type\": \"code_execution_20250825\",
        \"name\": \"code_execution\"
      }]
    }")

  STOP_REASON=$(echo "$RESPONSE" | jq -r '.stop_reason')
done
```
</CodeGroup>

<Note>
响应可能包括 `pause_turn` 停止原因，这表示 API 暂停了长时间运行的 Skill 操作。您可以在后续请求中按原样提供响应以让 Claude 继续其轮次，或者修改内容以中断对话并提供额外指导。
</Note>

### 使用多个 Skills

在单个请求中组合多个 Skills 来处理复杂工作流：

<CodeGroup>
```python Python
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {
                "type": "anthropic",
                "skill_id": "xlsx",
                "version": "latest"
            },
            {
                "type": "anthropic",
                "skill_id": "pptx",
                "version": "latest"
            },
            {
                "type": "custom",
                "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv",
                "version": "latest"
            }
        ]
    },
    messages=[{
        "role": "user",
        "content": "Analyze sales data and create a presentation"
    }],
    tools=[{
        "type": "code_execution_20250825",
        "name": "code_execution"
    }]
)
```

```typescript TypeScript
const response = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [
      {
        type: 'anthropic',
        skill_id: 'xlsx',
        version: 'latest'
      },
      {
        type: 'anthropic',
        skill_id: 'pptx',
        version: 'latest'
      },
      {
        type: 'custom',
        skill_id: 'skill_01AbCdEfGhIjKlMnOpQrStUv',
        version: 'latest'
      }
    ]
  },
  messages: [{
    role: 'user',
    content: 'Analyze sales data and create a presentation'
  }],
  tools: [{
    type: 'code_execution_20250825',
    name: 'code_execution'
  }]
});
```

```bash Shell
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "container": {
      "skills": [
        {
          "type": "anthropic",
          "skill_id": "xlsx",
          "version": "latest"
        },
        {
          "type": "anthropic",
          "skill_id": "pptx",
          "version": "latest"
        },
        {
          "type": "custom",
          "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv",
          "version": "latest"
        }
      ]
    },
    "messages": [{
      "role": "user",
      "content": "Analyze sales data and create a presentation"
    }],
    "tools": [{
      "type": "code_execution_20250825",
      "name": "code_execution"
    }]
  }'
```
</CodeGroup>

---

## 管理自定义 Skills

### 创建 Skill

上传您的自定义 Skill 以在您的工作区中使用。您可以使用目录路径或单个文件对象进行上传。

<CodeGroup>
```python Python
import anthropic

client = anthropic.Anthropic()

# 选项 1：使用 files_from_dir 助手（仅 Python，推荐）
from anthropic.lib import files_from_dir

skill = client.beta.skills.create(
    display_title="Financial Analysis",
    files=files_from_dir("/path/to/financial_analysis_skill"),
    betas=["skills-2025-10-02"]
)

# 选项 2：使用 zip 文件
skill = client.beta.skills.create(
    display_title="Financial Analysis",
    files=[("skill.zip", open("financial_analysis_skill.zip", "rb"))],
    betas=["skills-2025-10-02"]
)

# 选项 3：使用文件元组（文件名、文件内容、mime 类型）
skill = client.beta.skills.create(
    display_title="Financial Analysis",
    files=[
        ("financial_skill/SKILL.md", open("financial_skill/SKILL.md", "rb"), "text/markdown"),
        ("financial_skill/analyze.py", open("financial_skill/analyze.py", "rb"), "text/x-python"),
    ],
    betas=["skills-2025-10-02"]
)

print(f"Created skill: {skill.id}")
print(f"Latest version: {skill.latest_version}")
```

```typescript TypeScript
import Anthropic, { toFile } from '@anthropic-ai/sdk';
import fs from 'fs';

const client = new Anthropic();

// 选项 1：使用 zip 文件
const skill = await client.beta.skills.create({
  displayTitle: 'Financial Analysis',
  files: [
    await toFile(
      fs.createReadStream('financial_analysis_skill.zip'),
      'skill.zip'
    )
  ],
  betas: ['skills-2025-10-02']
});

// 选项 2：使用单个文件对象
const skill = await client.beta.skills.create({
  displayTitle: 'Financial Analysis',
  files: [
    await toFile(
      fs.createReadStream('financial_skill/SKILL.md'),
      'financial_skill/SKILL.md',
      { type: 'text/markdown' }
    ),
    await toFile(
      fs.createReadStream('financial_skill/analyze.py'),
      'financial_skill/analyze.py',
      { type: 'text/x-python' }
    ),
  ],
  betas: ['skills-2025-10-02']
});

console.log(`Created skill: ${skill.id}`);
console.log(`Latest version: ${skill.latest_version}`);
```

```bash Shell
curl -X POST "https://api.anthropic.com/v1/skills" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02" \
  -F "display_title=Financial Analysis" \
  -F "files[]=@financial_skill/SKILL.md;filename=financial_skill/SKILL.md" \
  -F "files[]=@financial_skill/analyze.py;filename=financial_skill/analyze.py"
```
</CodeGroup>

**要求：**
- 必须在顶级包含 SKILL.md 文件
- 所有文件必须在其路径中指定公共根目录
- 总上传大小必须在 8MB 以下
- YAML frontmatter 要求：
  - `name`：最多 64 个字符，仅小写字母/数字/连字符，无 XML 标签，无保留字（"anthropic"、"claude"）
  - `description`：最多 1024 个字符，非空，无 XML 标签

有关完整的请求/响应架构，请参阅 [Create Skill API 参考](/docs/zh-CN/api/skills/create-skill)。

### 列出 Skills

检索您的工作区可用的所有 Skills，包括 Anthropic 预构建 Skills 和您的自定义 Skills。使用 `source` 参数按 Skill 类型进行过滤：

<CodeGroup>
```python Python
# 列出所有 Skills
skills = client.beta.skills.list(
    betas=["skills-2025-10-02"]
)

for skill in skills.data:
    print(f"{skill.id}: {skill.display_title} (source: {skill.source})")

# 仅列出自定义 Skills
custom_skills = client.beta.skills.list(
    source="custom",
    betas=["skills-2025-10-02"]
)
```

```typescript TypeScript
// 列出所有 Skills
const skills = await client.beta.skills.list({
  betas: ['skills-2025-10-02']
});

for (const skill of skills.data) {
  console.log(`${skill.id}: ${skill.display_title} (source: ${skill.source})`);
}

// 仅列出自定义 Skills
const customSkills = await client.beta.skills.list({
  source: 'custom',
  betas: ['skills-2025-10-02']
});
```

```bash Shell
# 列出所有 Skills
curl "https://api.anthropic.com/v1/skills" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02"

# 仅列出自定义 Skills
curl "https://api.anthropic.com/v1/skills?source=custom" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02"
```
</CodeGroup>

有关分页和过滤选项，请参阅 [List Skills API 参考](/docs/zh-CN/api/skills/list-skills)。

### 检索 Skill

获取特定 Skill 的详情：

<CodeGroup>
```python Python
skill = client.beta.skills.retrieve(
    skill_id="skill_01AbCdEfGhIjKlMnOpQrStUv",
    betas=["skills-2025-10-02"]
)

print(f"Skill: {skill.display_title}")
print(f"Latest version: {skill.latest_version}")
print(f"Created: {skill.created_at}")
```

```typescript TypeScript
const skill = await client.beta.skills.retrieve(
  'skill_01AbCdEfGhIjKlMnOpQrStUv',
  { betas: ['skills-2025-10-02'] }
);

console.log(`Skill: ${skill.display_title}`);
console.log(`Latest version: ${skill.latest_version}`);
console.log(`Created: ${skill.created_at}`);
```

```bash Shell
curl "https://api.anthropic.com/v1/skills/skill_01AbCdEfGhIjKlMnOpQrStUv" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02"
```
</CodeGroup>

### 删除 Skill

要删除 Skill，您必须首先删除其所有版本：

<CodeGroup>
```python Python
# 步骤 1：删除所有版本
versions = client.beta.skills.versions.list(
    skill_id="skill_01AbCdEfGhIjKlMnOpQrStUv",
    betas=["skills-2025-10-02"]
)

for version in versions.data:
    client.beta.skills.versions.delete(
        skill_id="skill_01AbCdEfGhIjKlMnOpQrStUv",
        version=version.version,
        betas=["skills-2025-10-02"]
    )

# 步骤 2：删除 Skill
client.beta.skills.delete(
    skill_id="skill_01AbCdEfGhIjKlMnOpQrStUv",
    betas=["skills-2025-10-02"]
)
```

```typescript TypeScript
// 步骤 1：删除所有版本
const versions = await client.beta.skills.versions.list(
  'skill_01AbCdEfGhIjKlMnOpQrStUv',
  { betas: ['skills-2025-10-02'] }
);

for (const version of versions.data) {
  await client.beta.skills.versions.delete(
    'skill_01AbCdEfGhIjKlMnOpQrStUv',
    version.version,
    { betas: ['skills-2025-10-02'] }
  );
}

// 步骤 2：删除 Skill
await client.beta.skills.delete(
  'skill_01AbCdEfGhIjKlMnOpQrStUv',
  { betas: ['skills-2025-10-02'] }
);
```

```bash Shell
# 首先删除所有版本，然后删除 Skill
curl -X DELETE "https://api.anthropic.com/v1/skills/skill_01AbCdEfGhIjKlMnOpQrStUv" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02"
```
</CodeGroup>

尝试删除具有现有版本的 Skill 将返回 400 错误。

### 版本控制

Skills 支持版本控制以安全地管理更新：

**Anthropic 管理的 Skills**：
- 版本使用日期格式：`20251013`
- 进行更新时发布新版本
- 指定确切版本以获得稳定性

**自定义 Skills**：
- 自动生成的纪元时间戳：`1759178010641129`
- 使用 `"latest"` 始终获取最新版本
- 更新 Skill 文件时创建新版本

<CodeGroup>
```python Python
# 创建新版本
from anthropic.lib import files_from_dir

new_version = client.beta.skills.versions.create(
    skill_id="skill_01AbCdEfGhIjKlMnOpQrStUv",
    files=files_from_dir("/path/to/updated_skill"),
    betas=["skills-2025-10-02"]
)

# 使用特定版本
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{
            "type": "custom",
            "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv",
            "version": new_version.version
        }]
    },
    messages=[{"role": "user", "content": "Use updated Skill"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

# 使用最新版本
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{
            "type": "custom",
            "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv",
            "version": "latest"
        }]
    },
    messages=[{"role": "user", "content": "Use latest Skill version"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

```typescript TypeScript
// 使用 zip 文件创建新版本
const fs = require('fs');

const newVersion = await client.beta.skills.versions.create(
  'skill_01AbCdEfGhIjKlMnOpQrStUv',
  {
    files: [
      fs.createReadStream('updated_skill.zip')
    ],
    betas: ['skills-2025-10-02']
  }
);

// 使用特定版本
const response = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [{
      type: 'custom',
      skill_id: 'skill_01AbCdEfGhIjKlMnOpQrStUv',
      version: newVersion.version
    }]
  },
  messages: [{role: 'user', content: 'Use updated Skill'}],
  tools: [{type: 'code_execution_20250825', name: 'code_execution'}]
});

// 使用最新版本
const response = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [{
      type: 'custom',
      skill_id: 'skill_01AbCdEfGhIjKlMnOpQrStUv',
      version: 'latest'
    }]
  },
  messages: [{role: 'user', content: 'Use latest Skill version'}],
  tools: [{type: 'code_execution_20250825', name: 'code_execution'}]
});
```

```bash Shell
# 创建新版本
NEW_VERSION=$(curl -X POST "https://api.anthropic.com/v1/skills/skill_01AbCdEfGhIjKlMnOpQrStUv/versions" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02" \
  -F "files[]=@updated_skill/SKILL.md;filename=updated_skill/SKILL.md")

VERSION_NUMBER=$(echo "$NEW_VERSION" | jq -r '.version')

# 使用特定版本
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -H "content-type: application/json" \
  -d "{
    \"model\": \"claude-sonnet-4-5-20250929\",
    \"max_tokens\": 4096,
    \"container\": {
      \"skills\": [{
        \"type\": \"custom\",
        \"skill_id\": \"skill_01AbCdEfGhIjKlMnOpQrStUv\",
        \"version\": \"$VERSION_NUMBER\"
      }]
    },
    \"messages\": [{\"role\": \"user\", \"content\": \"Use updated Skill\"}],
    \"tools\": [{\"type\": \"code_execution_20250825\", \"name\": \"code_execution\"}]
  }"

# 使用最新版本
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "container": {
      "skills": [{
        "type": "custom",
        "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv",
        "version": "latest"
      }]
    },
    "messages": [{"role": "user", "content": "Use latest Skill version"}],
    "tools": [{"type": "code_execution_20250825", "name": "code_execution"}]
  }'
```
</CodeGroup>

有关完整详情，请参阅 [Create Skill Version API 参考](/docs/zh-CN/api/skills/create-skill-version)。

---

## Skills 如何加载

当您在容器中指定 Skills 时：

1. **元数据发现**：Claude 在系统提示中看到每个 Skill 的元数据（名称、描述）
2. **文件加载**：Skill 文件被复制到容器中的 `/skills/{directory}/`
3. **自动使用**：Claude 在与您的请求相关时自动加载和使用 Skills
4. **组合**：多个 Skills 为复杂工作流组合在一起

渐进式披露架构确保高效的上下文使用——Claude 仅在需要时加载完整的 Skill 指令。

---

## 用例

### 组织 Skills

**品牌与通信**
- 将公司特定的格式（颜色、字体、布局）应用于文档
- 生成遵循组织模板的通信
- 确保所有输出中的一致品牌指南

**项目管理**
- 使用公司特定格式（OKR、决策日志）构建笔记
- 生成遵循团队约定的任务
- 创建标准化的会议记录和状态更新

**业务运营**
- 创建公司标准报告、提案和分析
- 执行公司特定的分析程序
- 生成遵循组织模板的财务模型

### 个人 Skills

**内容创建**
- 自定义文档模板
- 专业格式和样式
- 特定领域的内容生成

**数据分析**
- 自定义数据处理管道
- 专业可视化模板
- 行业特定的分析方法

**开发与自动化**
- 代码生成模板
- 测试框架
- 部署工作流

### 示例：财务建模

组合 Excel 和自定义 DCF 分析 Skills：

<CodeGroup>
```python Python
# 创建自定义 DCF 分析 Skill
from anthropic.lib import files_from_dir

dcf_skill = client.beta.skills.create(
    display_title="DCF Analysis",
    files=files_from_dir("/path/to/dcf_skill"),
    betas=["skills-2025-10-02"]
)

# 与 Excel 一起使用以创建财务模型
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
            {"type": "custom", "skill_id": dcf_skill.id, "version": "latest"}
        ]
    },
    messages=[{
        "role": "user",
        "content": "Build a DCF valuation model for a SaaS company with the attached financials"
    }],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

```typescript TypeScript
// 创建自定义 DCF 分析 Skill
import { toFile } from '@anthropic-ai/sdk';
import fs from 'fs';

const dcfSkill = await client.beta.skills.create({
  displayTitle: 'DCF Analysis',
  files: [
    await toFile(fs.createReadStream('dcf_skill.zip'), 'skill.zip')
  ],
  betas: ['skills-2025-10-02']
});

// 与 Excel 一起使用以创建财务模型
const response = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
  container: {
    skills: [
      {type: 'anthropic', skill_id: 'xlsx', version: 'latest'},
      {type: 'custom', skill_id: dcfSkill.id, version: 'latest'}
    ]
  },
  messages: [{
    role: 'user',
    content: 'Build a DCF valuation model for a SaaS company with the attached financials'
  }],
  tools: [{type: 'code_execution_20250825', name: 'code_execution'}]
});
```

```bash Shell
# 创建自定义 DCF 分析 Skill
DCF_SKILL=$(curl -X POST "https://api.anthropic.com/v1/skills" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: skills-2025-10-02" \
  -F "display_title=DCF Analysis" \
  -F "files[]=@dcf_skill/SKILL.md;filename=dcf_skill/SKILL.md")

DCF_SKILL_ID=$(echo "$DCF_SKILL" | jq -r '.id')

# 与 Excel 一起使用以创建财务模型
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02" \
  -H "content-type: application/json" \
  -d "{
    \"model\": \"claude-sonnet-4-5-20250929\",
    \"max_tokens\": 4096,
    \"container\": {
      \"skills\": [
        {
          \"type\": \"anthropic\",
          \"skill_id\": \"xlsx\",
          \"version\": \"latest\"
        },
        {
          \"type\": \"custom\",
          \"skill_id\": \"$DCF_SKILL_ID\",
          \"version\": \"latest\"
        }
      ]
    },
    \"messages\": [{
      \"role\": \"user\",
      \"content\": \"Build a DCF valuation model for a SaaS company with the attached financials\"
    }],
    \"tools\": [{
      \"type\": \"code_execution_20250825\",
      \"name\": \"code_execution\"
    }]
  }"
```
</CodeGroup>

---

## 限制和约束

### 请求限制
- **每个请求的最大 Skills 数**：8
- **最大 Skill 上传大小**：8MB（所有文件合计）
- **YAML frontmatter 要求**：
  - `name`：最多 64 个字符，仅小写字母/数字/连字符，无 XML 标签，无保留字
  - `description`：最多 1024 个字符，非空，无 XML 标签

### 环境约束
Skills 在代码执行容器中运行，具有以下限制：
- **无网络访问** - 无法进行外部 API 调用
- **无运行时包安装** - 仅可用预安装的包
- **隔离环境** - 每个请求获得一个新容器

有关可用包，请参阅 [代码执行工具文档](/docs/zh-CN/agents-and-tools/tool-use/code-execution-tool)。

---

## 最佳实践

### 何时使用多个 Skills

当任务涉及多种文档类型或域时组合 Skills：

**良好用例：**
- 数据分析（Excel）+ 演示文稿创建（PowerPoint）
- 报告生成（Word）+ 导出为 PDF
- 自定义域逻辑 + 文档生成

**避免：**
- 包含未使用的 Skills（影响性能）

### 版本管理策略

**对于生产环境：**
```python
# 固定到特定版本以获得稳定性
container={
    "skills": [{
        "type": "custom",
        "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv",
        "version": "1759178010641129"  # 特定版本
    }]
}
```

**对于开发：**
```python
# 在活跃开发中使用最新版本
container={
    "skills": [{
        "type": "custom",
        "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv",
        "version": "latest"  # 始终获取最新版本
    }]
}
```

### 提示缓存注意事项

使用提示缓存时，请注意更改容器中的 Skills 列表将破坏缓存：

<CodeGroup>
```python Python
# 第一个请求创建缓存
response1 = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02", "prompt-caching-2024-07-31"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    messages=[{"role": "user", "content": "Analyze sales data"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)

# 添加/删除 Skills 会破坏缓存
response2 = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02", "prompt-caching-2024-07-31"],
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
            {"type": "anthropic", "skill_id": "pptx", "version": "latest"}  # 缓存未命中
        ]
    },
    messages=[{"role": "user", "content": "Create a presentation"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
)
```

```typescript TypeScript
// 第一个请求创建缓存
const response1 = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02', 'prompt-caching-2024-07-31'],
  container: {
    skills: [
      {type: 'anthropic', skill_id: 'xlsx', version: 'latest'}
    ]
  },
  messages: [{role: 'user', content: 'Analyze sales data'}],
  tools: [{type: 'code_execution_20250825', name: 'code_execution'}]
});

// 添加/删除 Skills 会破坏缓存
const response2 = await client.beta.messages.create({
  model: 'claude-sonnet-4-5-20250929',
  max_tokens: 4096,
  betas: ['code-execution-2025-08-25', 'skills-2025-10-02', 'prompt-caching-2024-07-31'],
  container: {
    skills: [
      {type: 'anthropic', skill_id: 'xlsx', version: 'latest'},
      {type: 'anthropic', skill_id: 'pptx', version: 'latest'}  // 缓存未命中
    ]
  },
  messages: [{role: 'user', content: 'Create a presentation'}],
  tools: [{type: 'code_execution_20250825', name: 'code_execution'}]
});
```

```bash Shell
# 第一个请求创建缓存
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02,prompt-caching-2024-07-31" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "container": {
      "skills": [
        {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
      ]
    },
    "messages": [{"role": "user", "content": "Analyze sales data"}],
    "tools": [{"type": "code_execution_20250825", "name": "code_execution"}]
  }'

# 添加/删除 Skills 会破坏缓存
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: code-execution-2025-08-25,skills-2025-10-02,prompt-caching-2024-07-31" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 4096,
    "container": {
      "skills": [
        {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
        {"type": "anthropic", "skill_id": "pptx", "version": "latest"}
      ]
    },
    "messages": [{"role": "user", "content": "Create a presentation"}],
    "tools": [{"type": "code_execution_20250825", "name": "code_execution"}]
  }'
```
</CodeGroup>

为了获得最佳缓存性能，请在请求中保持 Skills 列表一致。

### 错误处理

优雅地处理与 Skill 相关的错误：

<CodeGroup>
```python Python
try:
    response = client.beta.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        betas=["code-execution-2025-08-25", "skills-2025-10-02"],
        container={
            "skills": [
                {"type": "custom", "skill_id": "skill_01AbCdEfGhIjKlMnOpQrStUv", "version": "latest"}
            ]
        },
        messages=[{"role": "user", "content": "Process data"}],
        tools=[{"type": "code_execution_20250825", "name": "code_execution"}]
    )
except anthropic.BadRequestError as e:
    if "skill" in str(e):
        print(f"Skill error: {e}")
        # 处理 Skill 特定错误
    else:
        raise
```

```typescript TypeScript
try {
  const response = await client.beta.messages.create({
    model: 'claude-sonnet-4-5-20250929',
    max_tokens: 4096,
    betas: ['code-execution-2025-08-25', 'skills-2025-10-02'],
    container: {
      skills: [
        {type: 'custom', skill_id: 'skill_01AbCdEfGhIjKlMnOpQrStUv', version: 'latest'}
      ]
    },
    messages: [{role: 'user', content: 'Process data'}],
    tools: [{type: 'code_execution_20250825', name: 'code_execution'}]
  });
} catch (error) {
  if (error instanceof Anthropic.BadRequestError && error.message.includes('skill')) {
    console.error(`Skill error: ${error.message}`);
    // 处理 Skill 特定错误
  } else {
    throw error;
  }
}
```
</CodeGroup>

---

## 后续步骤

<CardGroup cols={2}>
  <Card
    title="API 参考"
    icon="book"
    href="/docs/zh-CN/api/skills/create-skill"
  >
    包含所有端点的完整 API 参考
  </Card>
  <Card
    title="编写指南"
    icon="edit"
    href="/docs/zh-CN/agents-and-tools/agent-skills/best-practices"
  >
    编写有效 Skills 的最佳实践
  </Card>
  <Card
    title="代码执行工具"
    icon="terminal"
    href="/docs/zh-CN/agents-and-tools/tool-use/code-execution-tool"
  >
    了解代码执行环境
  </Card>
</CardGroup>