<template>
  <div class="settings-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Setting /></el-icon>
            系统设置
          </h1>
          <p class="page-description">管理系统配置和偏好设置</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="saveAllSettings" :loading="saving">
            <el-icon><Check /></el-icon>
            保存所有设置
          </el-button>
          <el-button @click="resetSettings">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </div>
      </div>
    </div>
    
    <div class="settings-container">
      <el-row :gutter="20">
        <!-- 左侧导航 -->
        <el-col :xs="24" :sm="6" :md="5">
          <div class="settings-nav">
            <el-menu
              v-model:default-active="activeTab"
              mode="vertical"
              @select="handleTabChange"
            >
              <el-menu-item index="basic">
                <el-icon><Setting /></el-icon>
                <span>基本设置</span>
              </el-menu-item>
              <el-menu-item index="security">
                <el-icon><Lock /></el-icon>
                <span>安全设置</span>
              </el-menu-item>
              <el-menu-item index="notification">
                <el-icon><Bell /></el-icon>
                <span>通知设置</span>
              </el-menu-item>
              <el-menu-item index="system">
                <el-icon><Monitor /></el-icon>
                <span>系统配置</span>
              </el-menu-item>
              <el-menu-item index="storage">
                <el-icon><FolderOpened /></el-icon>
                <span>存储设置</span>
              </el-menu-item>
              <el-menu-item index="api">
                <el-icon><Connection /></el-icon>
                <span>API配置</span>
              </el-menu-item>
              <el-menu-item index="backup">
                <el-icon><Download /></el-icon>
                <span>备份恢复</span>
              </el-menu-item>
              <el-menu-item index="logs">
                <el-icon><Document /></el-icon>
                <span>日志设置</span>
              </el-menu-item>
            </el-menu>
          </div>
        </el-col>
        
        <!-- 右侧内容 -->
        <el-col :xs="24" :sm="18" :md="19">
          <div class="settings-content">
            <!-- 基本设置 -->
            <div v-show="activeTab === 'basic'" class="setting-section">
              <el-card shadow="never">
                <template #header>
                  <div class="section-header">
                    <h3>基本设置</h3>
                    <p>配置系统的基本信息和显示选项</p>
                  </div>
                </template>
                
                <el-form :model="basicSettings" label-width="120px">
                  <el-form-item label="系统名称">
                    <el-input
                      v-model="basicSettings.systemName"
                      placeholder="请输入系统名称"
                      style="width: 300px"
                    />
                  </el-form-item>
                  
                  <el-form-item label="系统描述">
                    <el-input
                      v-model="basicSettings.systemDescription"
                      type="textarea"
                      :rows="3"
                      placeholder="请输入系统描述"
                      style="width: 400px"
                    />
                  </el-form-item>
                  
                  <el-form-item label="系统Logo">
                    <div class="logo-upload">
                      <el-upload
                        class="logo-uploader"
                        action="#"
                        :show-file-list="false"
                        :before-upload="beforeLogoUpload"
                        :on-success="handleLogoSuccess"
                      >
                        <img v-if="basicSettings.logoUrl" :src="basicSettings.logoUrl" class="logo" />
                        <el-icon v-else class="logo-uploader-icon"><Plus /></el-icon>
                      </el-upload>
                      <div class="logo-tips">
                        <p>建议尺寸：200x60px，支持 JPG、PNG 格式</p>
                      </div>
                    </div>
                  </el-form-item>
                  
                  <el-form-item label="默认语言">
                    <el-select
                      v-model="basicSettings.defaultLanguage"
                      style="width: 200px"
                    >
                      <el-option label="简体中文" value="zh-CN" />
                      <el-option label="English" value="en-US" />
                      <el-option label="日本語" value="ja-JP" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="时区设置">
                    <el-select
                      v-model="basicSettings.timezone"
                      style="width: 250px"
                      filterable
                    >
                      <el-option label="Asia/Shanghai (UTC+8)" value="Asia/Shanghai" />
                      <el-option label="America/New_York (UTC-5)" value="America/New_York" />
                      <el-option label="Europe/London (UTC+0)" value="Europe/London" />
                      <el-option label="Asia/Tokyo (UTC+9)" value="Asia/Tokyo" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="日期格式">
                    <el-radio-group v-model="basicSettings.dateFormat">
                      <el-radio label="YYYY-MM-DD">2024-01-21</el-radio>
                      <el-radio label="MM/DD/YYYY">01/21/2024</el-radio>
                      <el-radio label="DD/MM/YYYY">21/01/2024</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  
                  <el-form-item label="主题设置">
                    <el-radio-group v-model="basicSettings.theme">
                      <el-radio label="light">浅色主题</el-radio>
                      <el-radio label="dark">深色主题</el-radio>
                      <el-radio label="auto">跟随系统</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  
                  <el-form-item label="页面大小">
                    <el-select
                      v-model="basicSettings.pageSize"
                      style="width: 150px"
                    >
                      <el-option label="10条/页" :value="10" />
                      <el-option label="20条/页" :value="20" />
                      <el-option label="50条/页" :value="50" />
                      <el-option label="100条/页" :value="100" />
                    </el-select>
                  </el-form-item>
                </el-form>
              </el-card>
            </div>
            
            <!-- 安全设置 -->
            <div v-show="activeTab === 'security'" class="setting-section">
              <el-card shadow="never">
                <template #header>
                  <div class="section-header">
                    <h3>安全设置</h3>
                    <p>配置系统安全策略和访问控制</p>
                  </div>
                </template>
                
                <el-form :model="securitySettings" label-width="150px">
                  <el-form-item label="密码策略">
                    <div class="password-policy">
                      <el-checkbox v-model="securitySettings.passwordPolicy.requireUppercase">
                        要求包含大写字母
                      </el-checkbox>
                      <el-checkbox v-model="securitySettings.passwordPolicy.requireLowercase">
                        要求包含小写字母
                      </el-checkbox>
                      <el-checkbox v-model="securitySettings.passwordPolicy.requireNumbers">
                        要求包含数字
                      </el-checkbox>
                      <el-checkbox v-model="securitySettings.passwordPolicy.requireSpecialChars">
                        要求包含特殊字符
                      </el-checkbox>
                    </div>
                  </el-form-item>
                  
                  <el-form-item label="最小密码长度">
                    <el-input-number
                      v-model="securitySettings.minPasswordLength"
                      :min="6"
                      :max="32"
                      style="width: 150px"
                    />
                    <span class="form-tip">字符</span>
                  </el-form-item>
                  
                  <el-form-item label="密码有效期">
                    <el-input-number
                      v-model="securitySettings.passwordExpireDays"
                      :min="0"
                      :max="365"
                      style="width: 150px"
                    />
                    <span class="form-tip">天（0表示永不过期）</span>
                  </el-form-item>
                  
                  <el-form-item label="登录失败锁定">
                    <el-switch
                      v-model="securitySettings.enableLoginLock"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <el-form-item label="最大失败次数" v-if="securitySettings.enableLoginLock">
                    <el-input-number
                      v-model="securitySettings.maxLoginAttempts"
                      :min="3"
                      :max="10"
                      style="width: 150px"
                    />
                    <span class="form-tip">次</span>
                  </el-form-item>
                  
                  <el-form-item label="锁定时间" v-if="securitySettings.enableLoginLock">
                    <el-input-number
                      v-model="securitySettings.lockDuration"
                      :min="5"
                      :max="1440"
                      style="width: 150px"
                    />
                    <span class="form-tip">分钟</span>
                  </el-form-item>
                  
                  <el-form-item label="会话超时">
                    <el-input-number
                      v-model="securitySettings.sessionTimeout"
                      :min="30"
                      :max="1440"
                      style="width: 150px"
                    />
                    <span class="form-tip">分钟</span>
                  </el-form-item>
                  
                  <el-form-item label="双因子认证">
                    <el-switch
                      v-model="securitySettings.enableTwoFactor"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <el-form-item label="IP白名单">
                    <el-switch
                      v-model="securitySettings.enableIpWhitelist"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <el-form-item label="允许的IP" v-if="securitySettings.enableIpWhitelist">
                    <el-input
                      v-model="securitySettings.ipWhitelist"
                      type="textarea"
                      :rows="3"
                      placeholder="每行一个IP地址或IP段，例如：192.168.1.1 或 192.168.1.0/24"
                      style="width: 400px"
                    />
                  </el-form-item>
                </el-form>
              </el-card>
            </div>
            
            <!-- 通知设置 -->
            <div v-show="activeTab === 'notification'" class="setting-section">
              <el-card shadow="never">
                <template #header>
                  <div class="section-header">
                    <h3>通知设置</h3>
                    <p>配置系统通知和消息推送</p>
                  </div>
                </template>
                
                <el-form :model="notificationSettings" label-width="150px">
                  <el-form-item label="邮件通知">
                    <el-switch
                      v-model="notificationSettings.enableEmail"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <div v-if="notificationSettings.enableEmail" class="email-config">
                    <el-form-item label="SMTP服务器">
                      <el-input
                        v-model="notificationSettings.email.smtpHost"
                        placeholder="smtp.example.com"
                        style="width: 300px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="SMTP端口">
                      <el-input-number
                        v-model="notificationSettings.email.smtpPort"
                        :min="1"
                        :max="65535"
                        style="width: 150px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="发送邮箱">
                      <el-input
                        v-model="notificationSettings.email.fromEmail"
                        placeholder="noreply@example.com"
                        style="width: 300px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="邮箱密码">
                      <el-input
                        v-model="notificationSettings.email.password"
                        type="password"
                        placeholder="请输入邮箱密码或授权码"
                        style="width: 300px"
                        show-password
                      />
                    </el-form-item>
                    
                    <el-form-item label="SSL加密">
                      <el-switch
                        v-model="notificationSettings.email.useSSL"
                        active-text="启用"
                        inactive-text="禁用"
                      />
                    </el-form-item>
                    
                    <el-form-item>
                      <el-button @click="testEmailConfig" :loading="testingEmail">
                        测试邮件配置
                      </el-button>
                    </el-form-item>
                  </div>
                  
                  <el-form-item label="通知类型">
                    <div class="notification-types">
                      <el-checkbox v-model="notificationSettings.types.userRegistration">
                        用户注册
                      </el-checkbox>
                      <el-checkbox v-model="notificationSettings.types.modelUpload">
                        模型上传
                      </el-checkbox>
                      <el-checkbox v-model="notificationSettings.types.trainingComplete">
                        训练完成
                      </el-checkbox>
                      <el-checkbox v-model="notificationSettings.types.deploymentStatus">
                        部署状态变更
                      </el-checkbox>
                      <el-checkbox v-model="notificationSettings.types.systemError">
                        系统错误
                      </el-checkbox>
                      <el-checkbox v-model="notificationSettings.types.securityAlert">
                        安全警报
                      </el-checkbox>
                    </div>
                  </el-form-item>
                  
                  <el-form-item label="通知频率">
                    <el-radio-group v-model="notificationSettings.frequency">
                      <el-radio label="immediate">立即发送</el-radio>
                      <el-radio label="hourly">每小时汇总</el-radio>
                      <el-radio label="daily">每日汇总</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  
                  <el-form-item label="管理员邮箱">
                    <el-input
                      v-model="notificationSettings.adminEmails"
                      type="textarea"
                      :rows="2"
                      placeholder="每行一个邮箱地址"
                      style="width: 400px"
                    />
                  </el-form-item>
                </el-form>
              </el-card>
            </div>
            
            <!-- 系统配置 -->
            <div v-show="activeTab === 'system'" class="setting-section">
              <el-card shadow="never">
                <template #header>
                  <div class="section-header">
                    <h3>系统配置</h3>
                    <p>配置系统运行参数和性能设置</p>
                  </div>
                </template>
                
                <el-form :model="systemSettings" label-width="150px">
                  <el-form-item label="调试模式">
                    <el-switch
                      v-model="systemSettings.debugMode"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                    <span class="form-tip">启用后会输出详细的调试信息</span>
                  </el-form-item>
                  
                  <el-form-item label="最大并发任务">
                    <el-input-number
                      v-model="systemSettings.maxConcurrentTasks"
                      :min="1"
                      :max="100"
                      style="width: 150px"
                    />
                    <span class="form-tip">个</span>
                  </el-form-item>
                  
                  <el-form-item label="任务超时时间">
                    <el-input-number
                      v-model="systemSettings.taskTimeout"
                      :min="60"
                      :max="86400"
                      style="width: 150px"
                    />
                    <span class="form-tip">秒</span>
                  </el-form-item>
                  
                  <el-form-item label="GPU内存限制">
                    <el-input-number
                      v-model="systemSettings.gpuMemoryLimit"
                      :min="1"
                      :max="80"
                      style="width: 150px"
                    />
                    <span class="form-tip">GB</span>
                  </el-form-item>
                  
                  <el-form-item label="自动清理">
                    <el-switch
                      v-model="systemSettings.autoCleanup"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <el-form-item label="清理间隔" v-if="systemSettings.autoCleanup">
                    <el-input-number
                      v-model="systemSettings.cleanupInterval"
                      :min="1"
                      :max="30"
                      style="width: 150px"
                    />
                    <span class="form-tip">天</span>
                  </el-form-item>
                  
                  <el-form-item label="监控采样率">
                    <el-input-number
                      v-model="systemSettings.monitoringSampleRate"
                      :min="1"
                      :max="60"
                      style="width: 150px"
                    />
                    <span class="form-tip">秒</span>
                  </el-form-item>
                  
                  <el-form-item label="API限流">
                    <el-switch
                      v-model="systemSettings.enableRateLimit"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <el-form-item label="每分钟请求数" v-if="systemSettings.enableRateLimit">
                    <el-input-number
                      v-model="systemSettings.rateLimit"
                      :min="10"
                      :max="10000"
                      style="width: 150px"
                    />
                    <span class="form-tip">次/分钟</span>
                  </el-form-item>
                </el-form>
              </el-card>
            </div>
            
            <!-- 存储设置 -->
            <div v-show="activeTab === 'storage'" class="setting-section">
              <el-card shadow="never">
                <template #header>
                  <div class="section-header">
                    <h3>存储设置</h3>
                    <p>配置文件存储和数据管理</p>
                  </div>
                </template>
                
                <el-form :model="storageSettings" label-width="150px">
                  <el-form-item label="存储类型">
                    <el-radio-group v-model="storageSettings.type">
                      <el-radio label="local">本地存储</el-radio>
                      <el-radio label="s3">Amazon S3</el-radio>
                      <el-radio label="oss">阿里云OSS</el-radio>
                      <el-radio label="cos">腾讯云COS</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  
                  <div v-if="storageSettings.type === 'local'" class="storage-config">
                    <el-form-item label="存储路径">
                      <el-input
                        v-model="storageSettings.local.path"
                        placeholder="/data/acwl-ai"
                        style="width: 400px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="最大存储空间">
                      <el-input-number
                        v-model="storageSettings.local.maxSize"
                        :min="1"
                        :max="10000"
                        style="width: 150px"
                      />
                      <span class="form-tip">GB</span>
                    </el-form-item>
                  </div>
                  
                  <div v-if="storageSettings.type === 's3'" class="storage-config">
                    <el-form-item label="Access Key">
                      <el-input
                        v-model="storageSettings.s3.accessKey"
                        placeholder="请输入Access Key"
                        style="width: 300px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="Secret Key">
                      <el-input
                        v-model="storageSettings.s3.secretKey"
                        type="password"
                        placeholder="请输入Secret Key"
                        style="width: 300px"
                        show-password
                      />
                    </el-form-item>
                    
                    <el-form-item label="Bucket名称">
                      <el-input
                        v-model="storageSettings.s3.bucket"
                        placeholder="my-bucket"
                        style="width: 300px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="区域">
                      <el-input
                        v-model="storageSettings.s3.region"
                        placeholder="us-east-1"
                        style="width: 200px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="自定义域名">
                      <el-input
                        v-model="storageSettings.s3.customDomain"
                        placeholder="https://cdn.example.com"
                        style="width: 300px"
                      />
                    </el-form-item>
                  </div>
                  
                  <el-form-item label="文件清理策略">
                    <el-radio-group v-model="storageSettings.cleanupPolicy">
                      <el-radio label="never">永不清理</el-radio>
                      <el-radio label="auto">自动清理</el-radio>
                      <el-radio label="manual">手动清理</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  
                  <el-form-item label="清理规则" v-if="storageSettings.cleanupPolicy === 'auto'">
                    <div class="cleanup-rules">
                      <el-checkbox v-model="storageSettings.cleanupRules.deleteOldModels">
                        删除30天前的未使用模型
                      </el-checkbox>
                      <el-checkbox v-model="storageSettings.cleanupRules.deleteOldLogs">
                        删除7天前的日志文件
                      </el-checkbox>
                      <el-checkbox v-model="storageSettings.cleanupRules.deleteOldBackups">
                        删除90天前的备份文件
                      </el-checkbox>
                      <el-checkbox v-model="storageSettings.cleanupRules.compressOldData">
                        压缩60天前的数据
                      </el-checkbox>
                    </div>
                  </el-form-item>
                  
                  <el-form-item>
                    <el-button @click="testStorageConfig" :loading="testingStorage">
                      测试存储配置
                    </el-button>
                    <el-button @click="viewStorageUsage">
                      查看存储使用情况
                    </el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </div>
            
            <!-- API配置 -->
            <div v-show="activeTab === 'api'" class="setting-section">
              <el-card shadow="never">
                <template #header>
                  <div class="section-header">
                    <h3>API配置</h3>
                    <p>配置API接口和第三方服务</p>
                  </div>
                </template>
                
                <el-form :model="apiSettings" label-width="150px">
                  <el-form-item label="API版本">
                    <el-select
                      v-model="apiSettings.version"
                      style="width: 150px"
                    >
                      <el-option label="v1" value="v1" />
                      <el-option label="v2" value="v2" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="API文档">
                    <el-switch
                      v-model="apiSettings.enableDocs"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                    <span class="form-tip">启用Swagger API文档</span>
                  </el-form-item>
                  
                  <el-form-item label="CORS设置">
                    <el-input
                      v-model="apiSettings.corsOrigins"
                      type="textarea"
                      :rows="2"
                      placeholder="每行一个域名，例如：https://example.com"
                      style="width: 400px"
                    />
                  </el-form-item>
                  
                  <el-form-item label="OpenAI API">
                    <el-switch
                      v-model="apiSettings.openai.enabled"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <div v-if="apiSettings.openai.enabled" class="api-config">
                    <el-form-item label="API Key">
                      <el-input
                        v-model="apiSettings.openai.apiKey"
                        type="password"
                        placeholder="sk-..."
                        style="width: 400px"
                        show-password
                      />
                    </el-form-item>
                    
                    <el-form-item label="Base URL">
                      <el-input
                        v-model="apiSettings.openai.baseUrl"
                        placeholder="https://api.openai.com/v1"
                        style="width: 400px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="默认模型">
                      <el-input
                        v-model="apiSettings.openai.defaultModel"
                        placeholder="gpt-3.5-turbo"
                        style="width: 200px"
                      />
                    </el-form-item>
                  </div>
                  
                  <el-form-item label="Hugging Face">
                    <el-switch
                      v-model="apiSettings.huggingface.enabled"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <div v-if="apiSettings.huggingface.enabled" class="api-config">
                    <el-form-item label="API Token">
                      <el-input
                        v-model="apiSettings.huggingface.token"
                        type="password"
                        placeholder="hf_..."
                        style="width: 400px"
                        show-password
                      />
                    </el-form-item>
                    
                    <el-form-item label="缓存目录">
                      <el-input
                        v-model="apiSettings.huggingface.cacheDir"
                        placeholder="/data/huggingface"
                        style="width: 300px"
                      />
                    </el-form-item>
                  </div>
                  
                  <el-form-item>
                    <el-button @click="testApiConfig" :loading="testingApi">
                      测试API配置
                    </el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </div>
            
            <!-- 备份恢复 -->
            <div v-show="activeTab === 'backup'" class="setting-section">
              <el-card shadow="never">
                <template #header>
                  <div class="section-header">
                    <h3>备份恢复</h3>
                    <p>管理系统数据备份和恢复</p>
                  </div>
                </template>
                
                <el-form :model="backupSettings" label-width="150px">
                  <el-form-item label="自动备份">
                    <el-switch
                      v-model="backupSettings.autoBackup"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <el-form-item label="备份频率" v-if="backupSettings.autoBackup">
                    <el-radio-group v-model="backupSettings.frequency">
                      <el-radio label="daily">每日</el-radio>
                      <el-radio label="weekly">每周</el-radio>
                      <el-radio label="monthly">每月</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  
                  <el-form-item label="备份时间" v-if="backupSettings.autoBackup">
                    <el-time-picker
                      v-model="backupSettings.backupTime"
                      format="HH:mm"
                      placeholder="选择备份时间"
                    />
                  </el-form-item>
                  
                  <el-form-item label="保留份数">
                    <el-input-number
                      v-model="backupSettings.retentionCount"
                      :min="1"
                      :max="30"
                      style="width: 150px"
                    />
                    <span class="form-tip">份</span>
                  </el-form-item>
                  
                  <el-form-item label="备份内容">
                    <div class="backup-content">
                      <el-checkbox v-model="backupSettings.includeDatabase">
                        数据库
                      </el-checkbox>
                      <el-checkbox v-model="backupSettings.includeModels">
                        模型文件
                      </el-checkbox>
                      <el-checkbox v-model="backupSettings.includeDatasets">
                        数据集
                      </el-checkbox>
                      <el-checkbox v-model="backupSettings.includeConfigs">
                        配置文件
                      </el-checkbox>
                      <el-checkbox v-model="backupSettings.includeLogs">
                        日志文件
                      </el-checkbox>
                    </div>
                  </el-form-item>
                  
                  <el-form-item label="压缩备份">
                    <el-switch
                      v-model="backupSettings.compress"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <el-form-item label="备份加密">
                    <el-switch
                      v-model="backupSettings.encrypt"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <el-form-item label="加密密码" v-if="backupSettings.encrypt">
                    <el-input
                      v-model="backupSettings.encryptPassword"
                      type="password"
                      placeholder="请输入加密密码"
                      style="width: 300px"
                      show-password
                    />
                  </el-form-item>
                  
                  <el-form-item>
                    <el-button type="primary" @click="createBackup" :loading="creatingBackup">
                      立即备份
                    </el-button>
                    <el-button @click="viewBackupHistory">
                      备份历史
                    </el-button>
                    <el-button @click="showRestoreDialog">
                      恢复数据
                    </el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </div>
            
            <!-- 日志设置 -->
            <div v-show="activeTab === 'logs'" class="setting-section">
              <el-card shadow="never">
                <template #header>
                  <div class="section-header">
                    <h3>日志设置</h3>
                    <p>配置系统日志记录和管理</p>
                  </div>
                </template>
                
                <el-form :model="logSettings" label-width="150px">
                  <el-form-item label="日志级别">
                    <el-select
                      v-model="logSettings.level"
                      style="width: 150px"
                    >
                      <el-option label="DEBUG" value="debug" />
                      <el-option label="INFO" value="info" />
                      <el-option label="WARN" value="warn" />
                      <el-option label="ERROR" value="error" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="日志格式">
                    <el-radio-group v-model="logSettings.format">
                      <el-radio label="json">JSON格式</el-radio>
                      <el-radio label="text">文本格式</el-radio>
                    </el-radio-group>
                  </el-form-item>
                  
                  <el-form-item label="日志输出">
                    <div class="log-outputs">
                      <el-checkbox v-model="logSettings.outputs.console">
                        控制台
                      </el-checkbox>
                      <el-checkbox v-model="logSettings.outputs.file">
                        文件
                      </el-checkbox>
                      <el-checkbox v-model="logSettings.outputs.database">
                        数据库
                      </el-checkbox>
                    </div>
                  </el-form-item>
                  
                  <el-form-item label="日志目录" v-if="logSettings.outputs.file">
                    <el-input
                      v-model="logSettings.logDir"
                      placeholder="/var/log/acwl-ai"
                      style="width: 300px"
                    />
                  </el-form-item>
                  
                  <el-form-item label="单文件大小" v-if="logSettings.outputs.file">
                    <el-input-number
                      v-model="logSettings.maxFileSize"
                      :min="1"
                      :max="1000"
                      style="width: 150px"
                    />
                    <span class="form-tip">MB</span>
                  </el-form-item>
                  
                  <el-form-item label="保留文件数" v-if="logSettings.outputs.file">
                    <el-input-number
                      v-model="logSettings.maxFiles"
                      :min="1"
                      :max="100"
                      style="width: 150px"
                    />
                    <span class="form-tip">个</span>
                  </el-form-item>
                  
                  <el-form-item label="日志保留期">
                    <el-input-number
                      v-model="logSettings.retentionDays"
                      :min="1"
                      :max="365"
                      style="width: 150px"
                    />
                    <span class="form-tip">天</span>
                  </el-form-item>
                  
                  <el-form-item label="敏感信息过滤">
                    <el-switch
                      v-model="logSettings.filterSensitive"
                      active-text="启用"
                      inactive-text="禁用"
                    />
                  </el-form-item>
                  
                  <el-form-item>
                    <el-button @click="viewLogs">
                      查看日志
                    </el-button>
                    <el-button @click="downloadLogs">
                      下载日志
                    </el-button>
                    <el-button @click="clearLogs" type="danger">
                      清空日志
                    </el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 恢复数据对话框 -->
    <el-dialog
      v-model="restoreDialogVisible"
      title="恢复数据"
      width="500px"
    >
      <el-form :model="restoreForm" label-width="100px">
        <el-form-item label="备份文件">
          <el-upload
            ref="uploadRef"
            action="#"
            :limit="1"
            :on-exceed="handleExceed"
            :auto-upload="false"
            accept=".zip,.tar.gz"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              选择备份文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 .zip 和 .tar.gz 格式的备份文件
              </div>
            </template>
          </el-upload>
        </el-form-item>
        
        <el-form-item label="恢复选项">
          <div class="restore-options">
            <el-checkbox v-model="restoreForm.restoreDatabase">
              恢复数据库
            </el-checkbox>
            <el-checkbox v-model="restoreForm.restoreModels">
              恢复模型文件
            </el-checkbox>
            <el-checkbox v-model="restoreForm.restoreConfigs">
              恢复配置文件
            </el-checkbox>
          </div>
        </el-form-item>
        
        <el-form-item label="解密密码" v-if="restoreForm.encrypted">
          <el-input
            v-model="restoreForm.password"
            type="password"
            placeholder="请输入解密密码"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="restoreDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="startRestore"
            :loading="restoring"
          >
            开始恢复
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type UploadInstance } from 'element-plus'
import {
  Setting,
  Check,
  RefreshLeft,
  Lock,
  Bell,
  Monitor,
  FolderOpened,
  Connection,
  Download,
  Document,
  Plus,
  Upload
} from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const activeTab = ref('basic')
const saving = ref(false)
const testingEmail = ref(false)
const testingStorage = ref(false)
const testingApi = ref(false)
const creatingBackup = ref(false)
const restoring = ref(false)
const restoreDialogVisible = ref(false)
const uploadRef = ref<UploadInstance>()

// 基本设置
const basicSettings = reactive({
  systemName: 'ACWL AI Platform',
  systemDescription: '智能AI模型训练与部署平台',
  logoUrl: '',
  defaultLanguage: 'zh-CN',
  timezone: 'Asia/Shanghai',
  dateFormat: 'YYYY-MM-DD',
  theme: 'light',
  pageSize: 20
})

// 安全设置
const securitySettings = reactive({
  passwordPolicy: {
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: false
  },
  minPasswordLength: 8,
  passwordExpireDays: 90,
  enableLoginLock: true,
  maxLoginAttempts: 5,
  lockDuration: 30,
  sessionTimeout: 120,
  enableTwoFactor: false,
  enableIpWhitelist: false,
  ipWhitelist: ''
})

// 通知设置
const notificationSettings = reactive({
  enableEmail: false,
  email: {
    smtpHost: '',
    smtpPort: 587,
    fromEmail: '',
    password: '',
    useSSL: true
  },
  types: {
    userRegistration: true,
    modelUpload: true,
    trainingComplete: true,
    deploymentStatus: true,
    systemError: true,
    securityAlert: true
  },
  frequency: 'immediate',
  adminEmails: ''
})

// 系统配置
const systemSettings = reactive({
  debugMode: false,
  maxConcurrentTasks: 10,
  taskTimeout: 3600,
  gpuMemoryLimit: 16,
  autoCleanup: true,
  cleanupInterval: 7,
  monitoringSampleRate: 30,
  enableRateLimit: true,
  rateLimit: 1000
})

// 存储设置
const storageSettings = reactive({
  type: 'local',
  local: {
    path: '/data/acwl-ai',
    maxSize: 1000
  },
  s3: {
    accessKey: '',
    secretKey: '',
    bucket: '',
    region: '',
    customDomain: ''
  },
  cleanupPolicy: 'auto',
  cleanupRules: {
    deleteOldModels: true,
    deleteOldLogs: true,
    deleteOldBackups: true,
    compressOldData: false
  }
})

// API配置
const apiSettings = reactive({
  version: 'v1',
  enableDocs: true,
  corsOrigins: '',
  openai: {
    enabled: false,
    apiKey: '',
    baseUrl: 'https://api.openai.com/v1',
    defaultModel: 'gpt-3.5-turbo'
  },
  huggingface: {
    enabled: false,
    token: '',
    cacheDir: '/data/huggingface'
  }
})

// 备份设置
const backupSettings = reactive({
  autoBackup: true,
  frequency: 'daily',
  backupTime: new Date(),
  retentionCount: 7,
  includeDatabase: true,
  includeModels: false,
  includeDatasets: false,
  includeConfigs: true,
  includeLogs: false,
  compress: true,
  encrypt: false,
  encryptPassword: ''
})

// 日志设置
const logSettings = reactive({
  level: 'info',
  format: 'json',
  outputs: {
    console: true,
    file: true,
    database: false
  },
  logDir: '/var/log/acwl-ai',
  maxFileSize: 100,
  maxFiles: 10,
  retentionDays: 30,
  filterSensitive: true
})

// 恢复表单
const restoreForm = reactive({
  restoreDatabase: true,
  restoreModels: false,
  restoreConfigs: true,
  encrypted: false,
  password: ''
})

// 方法
const handleTabChange = (key: string) => {
  activeTab.value = key
}

const beforeLogoUpload = (file: File) => {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB!')
    return false
  }
  return true
}

const handleLogoSuccess = (response: any, file: File) => {
  basicSettings.logoUrl = URL.createObjectURL(file)
  ElMessage.success('Logo上传成功')
}

const testEmailConfig = async () => {
  testingEmail.value = true
  try {
    // 这里应该调用实际的API测试邮件配置
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('邮件配置测试成功')
  } catch (error) {
    ElMessage.error('邮件配置测试失败')
  } finally {
    testingEmail.value = false
  }
}

const testStorageConfig = async () => {
  testingStorage.value = true
  try {
    // 这里应该调用实际的API测试存储配置
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('存储配置测试成功')
  } catch (error) {
    ElMessage.error('存储配置测试失败')
  } finally {
    testingStorage.value = false
  }
}

const viewStorageUsage = () => {
  router.push('/admin/storage')
}

const testApiConfig = async () => {
  testingApi.value = true
  try {
    // 这里应该调用实际的API测试配置
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('API配置测试成功')
  } catch (error) {
    ElMessage.error('API配置测试失败')
  } finally {
    testingApi.value = false
  }
}

const createBackup = async () => {
  creatingBackup.value = true
  try {
    // 这里应该调用实际的API创建备份
    await new Promise(resolve => setTimeout(resolve, 3000))
    ElMessage.success('备份创建成功')
  } catch (error) {
    ElMessage.error('备份创建失败')
  } finally {
    creatingBackup.value = false
  }
}

const viewBackupHistory = () => {
  router.push('/admin/backups')
}

const showRestoreDialog = () => {
  restoreDialogVisible.value = true
}

const handleExceed = () => {
  ElMessage.warning('只能选择一个备份文件')
}

const startRestore = async () => {
  restoring.value = true
  try {
    // 这里应该调用实际的API开始恢复
    await new Promise(resolve => setTimeout(resolve, 5000))
    ElMessage.success('数据恢复成功')
    restoreDialogVisible.value = false
  } catch (error) {
    ElMessage.error('数据恢复失败')
  } finally {
    restoring.value = false
  }
}

const viewLogs = () => {
  router.push('/admin/logs')
}

const downloadLogs = () => {
  // 这里应该调用实际的API下载日志
  ElMessage.success('日志下载已开始')
}

const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有日志吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API清空日志
    ElMessage.success('日志清空成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('日志清空失败')
    }
  }
}

const saveAllSettings = async () => {
  saving.value = true
  try {
    // 这里应该调用实际的API保存所有设置
    const settings = {
      basic: basicSettings,
      security: securitySettings,
      notification: notificationSettings,
      system: systemSettings,
      storage: storageSettings,
      api: apiSettings,
      backup: backupSettings,
      log: logSettings
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000))
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('设置保存失败')
  } finally {
    saving.value = false
  }
}

const resetSettings = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有设置为默认值吗？',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该重置所有设置为默认值
    ElMessage.success('设置重置成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('设置重置失败')
    }
  }
}

const loadSettings = async () => {
  try {
    // 这里应该调用实际的API加载设置
    // const response = await settingsApi.getSettings()
    // Object.assign(basicSettings, response.data.basic)
    // ...
  } catch (error) {
    console.error('加载设置失败:', error)
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style lang="scss" scoped>
.settings-page {
  padding: 20px;
  
  .page-header {
    margin-bottom: 20px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      
      .header-left {
        .page-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin: 0 0 8px 0;
        }
        
        .page-description {
          color: var(--el-text-color-regular);
          margin: 0;
        }
      }
      
      .header-right {
        display: flex;
        gap: 12px;
      }
    }
  }
  
  .settings-container {
    .settings-nav {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      
      :deep(.el-menu) {
        border: none;
        
        .el-menu-item {
          height: 48px;
          line-height: 48px;
          
          &.is-active {
            background-color: var(--el-color-primary-light-9);
            color: var(--el-color-primary);
          }
        }
      }
    }
    
    .settings-content {
      .setting-section {
        .section-header {
          h3 {
            font-size: 18px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin: 0 0 8px 0;
          }
          
          p {
            color: var(--el-text-color-regular);
            margin: 0;
          }
        }
        
        .form-tip {
          margin-left: 8px;
          color: var(--el-text-color-secondary);
          font-size: 12px;
        }
        
        .logo-upload {
          display: flex;
          align-items: flex-start;
          gap: 16px;
          
          .logo-uploader {
            :deep(.el-upload) {
              border: 1px dashed var(--el-border-color);
              border-radius: 6px;
              cursor: pointer;
              position: relative;
              overflow: hidden;
              transition: var(--el-transition-duration-fast);
              
              &:hover {
                border-color: var(--el-color-primary);
              }
            }
            
            .logo-uploader-icon {
              font-size: 28px;
              color: #8c939d;
              width: 200px;
              height: 60px;
              text-align: center;
              line-height: 60px;
            }
            
            .logo {
              width: 200px;
              height: 60px;
              display: block;
              object-fit: contain;
            }
          }
          
          .logo-tips {
            p {
              margin: 0;
              color: var(--el-text-color-secondary);
              font-size: 12px;
            }
          }
        }
        
        .password-policy {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .notification-types {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .email-config,
        .api-config,
        .storage-config {
          margin-left: 20px;
          padding: 16px;
          background: var(--el-fill-color-lighter);
          border-radius: 6px;
          border-left: 3px solid var(--el-color-primary);
        }
        
        .cleanup-rules {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .backup-content {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .log-outputs {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .restore-options {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .settings-page {
    padding: 16px;
    
    .page-header {
      .header-content {
        flex-direction: column;
        gap: 16px;
        
        .header-right {
          width: 100%;
          justify-content: flex-end;
        }
      }
    }
    
    .settings-container {
      .settings-nav {
        margin-bottom: 20px;
        
        :deep(.el-menu) {
          display: flex;
          overflow-x: auto;
          
          .el-menu-item {
            white-space: nowrap;
            min-width: 120px;
          }
        }
      }
      
      .settings-content {
        .setting-section {
          :deep(.el-form) {
            .el-form-item {
              .el-input,
              .el-select,
              .el-input-number {
                width: 100% !important;
              }
            }
          }
          
          .logo-upload {
            flex-direction: column;
            align-items: center;
          }
          
          .email-config,
          .api-config,
          .storage-config {
            margin-left: 0;
          }
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .settings-page {
    .settings-container {
      .settings-nav {
        background: var(--el-bg-color-page);
        border: 1px solid var(--el-border-color);
      }
      
      .settings-content {
        .setting-section {
          .email-config,
          .api-config,
          .storage-config {
            background: var(--el-fill-color-dark);
          }
        }
      }
    }
  }
}
</style>