<template>
  <div class="config-section">
    <h4>FTP传输配置</h4>
    
    <el-form-item label="服务器地址">
      <el-input 
        v-model="localConfig.host" 
        placeholder="ftp.example.com"
        @change="handleChange"
      />
    </el-form-item>

    <el-form-item label="端口">
      <el-input-number 
        v-model="localConfig.port" 
        :min="1" 
        :max="65535"
        @change="handleChange"
      />
    </el-form-item>
    
    <el-form-item label="用户名">
      <el-input 
        v-model="localConfig.username" 
        placeholder="Username"
        @change="handleChange"
      />
    </el-form-item>

    <el-form-item label="密码">
      <el-input 
        v-model="localConfig.password" 
        type="password"
        placeholder="Password"
        show-password
        @change="handleChange"
      />
    </el-form-item>

    <el-form-item label="传输模式">
      <el-radio-group v-model="localConfig.mode" @change="handleChange">
        <el-radio value="upload">上传</el-radio>
        <el-radio value="download">下载</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label="本地路径">
      <el-input 
        v-model="localConfig.localPath" 
        placeholder="/local/path/file"
        @change="handleChange"
      />
    </el-form-item>

    <el-form-item label="远程路径">
      <el-input 
        v-model="localConfig.remotePath" 
        placeholder="/remote/path/file"
        @change="handleChange"
      />
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const localConfig = ref({
  host: '',
  port: 21,
  username: '',
  password: '',
  mode: 'download',
  localPath: '',
  remotePath: '',
  ...props.modelValue
})

watch(() => props.modelValue, (newValue) => {
  localConfig.value = { 
    host: '',
    port: 21,
    username: '',
    password: '',
    mode: 'download',
    localPath: '',
    remotePath: '',
    ...newValue 
  }
}, { deep: true })

const handleChange = () => {
  emit('update:modelValue', localConfig.value)
  emit('change', localConfig.value)
}
</script>
