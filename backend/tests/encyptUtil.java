package cn.com.cepiec.af.until;

import cn.com.cepiec.af.entity.AfBaseart;
import com.google.gson.Gson;
import org.apache.commons.lang3.StringUtils;
import org.springframework.http.*;
import org.springframework.http.converter.StringHttpMessageConverter;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.client.RestTemplate;

import javax.crypto.Cipher;
import javax.crypto.Mac;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.*;

public class encryptUtil {

    /**
     * 随机字符串（如 8~16 位），用于增强请求唯一性
     *
     * @param minLen
     * @param maxLen
     * @return
     */
    public static String generateRandomString(int minLen, int maxLen) {
        String CHAR_POOL = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

        Random random = new Random();
        int length = minLen + random.nextInt(maxLen - minLen + 1); // 生成[minLen, maxLen]范围内的长度

        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            sb.append(CHAR_POOL.charAt(random.nextInt(CHAR_POOL.length())));
        }
        return sb.toString();
    }

    // 将字节数组转为十六进制字符串
    private static String bytesToHex(byte[] bytes) {
        StringBuilder hexString = new StringBuilder(2 * bytes.length);
        for (byte b : bytes) {
            hexString.append(String.format("%02x", b));
        }
        return hexString.toString();
    }

    public static String hmacSha256HexUpper(String key, String data) {
        try {
            // 创建 HMAC-SHA256 Mac 实例
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKeySpec = new SecretKeySpec(key.getBytes("UTF-8"), "HmacSHA256");
            mac.init(secretKeySpec);

            // 计算 HMAC
            byte[] hash = mac.doFinal(data.getBytes("UTF-8"));

            // 转为十六进制并大写
            return bytesToHex(hash).toUpperCase();
        } catch (Exception e) {
            throw new RuntimeException("HMAC SHA256加密失败", e);
        }
    }


    /**
     * 加密数据
     * @param dataList 数据列表（List<Map>）
     * @param base64Key Base64 编码的 256-bit AES 密钥
     * @return 加密结果（包含 Base64 编码的密文 和 IV）
     */
    public static Map<String, String> encrypt(List<Map<String, Object>> dataList, String base64Key) throws Exception {
        int GCM_TAG_LENGTH = 128; // 128位认证标签
        int IV_LENGTH = 12;       // 12字节IV
        String ALGORITHM = "AES/GCM/NoPadding";

        // 1. Base64 解码密钥
        byte[] keyBytes = Base64.getDecoder().decode(base64Key);
        SecretKey key = new SecretKeySpec(keyBytes, "AES");

        // 2. 生成随机 IV（12 字节）
        byte[] iv = new byte[IV_LENGTH];
        SecureRandom random = new SecureRandom();
        random.nextBytes(iv);

        // 3. 初始化加密器
        Cipher cipher = Cipher.getInstance(ALGORITHM);
        GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
        cipher.init(Cipher.ENCRYPT_MODE, key, gcmSpec);

        // 4. 序列化数据为 JSON 字符串
        Gson gson = new Gson();
        String jsonData = gson.toJson(dataList);
        byte[] plaintext = jsonData.getBytes(StandardCharsets.UTF_8);

        // 5. 加密数据，doFinal 输出 = ciphertext + tag
        byte[] encryptedBytes = cipher.doFinal(plaintext);

        // 6. 返回 Base64 编码结果
        Map<String, String> result = new HashMap<>();
        result.put("data", Base64.getEncoder().encodeToString(encryptedBytes));  // 密文 + tag
        result.put("iv", Base64.getEncoder().encodeToString(iv));                // IV
        return result;
    }

    public static Map<String, String> encrypt(Map<String, Object> dataList, String base64Key) throws Exception {
        int GCM_TAG_LENGTH = 128; // 128位认证标签
        int IV_LENGTH = 12;       // 12字节IV
        String ALGORITHM = "AES/GCM/NoPadding";

        // 1. Base64 解码密钥
        byte[] keyBytes = Base64.getDecoder().decode(base64Key);
        SecretKey key = new SecretKeySpec(keyBytes, "AES");

        // 2. 生成随机 IV（12 字节）
        byte[] iv = new byte[IV_LENGTH];
        SecureRandom random = new SecureRandom();
        random.nextBytes(iv);

        // 3. 初始化加密器
        Cipher cipher = Cipher.getInstance(ALGORITHM);
        GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
        cipher.init(Cipher.ENCRYPT_MODE, key, gcmSpec);

        // 4. 序列化数据为 JSON 字符串
        Gson gson = new Gson();
        String jsonData = gson.toJson(dataList);
        byte[] plaintext = jsonData.getBytes(StandardCharsets.UTF_8);

        // 5. 加密数据，doFinal 输出 = ciphertext + tag
        byte[] encryptedBytes = cipher.doFinal(plaintext);

        // 6. 返回 Base64 编码结果
        Map<String, String> result = new HashMap<>();
        result.put("data", Base64.getEncoder().encodeToString(encryptedBytes));  // 密文 + tag
        result.put("iv", Base64.getEncoder().encodeToString(iv));                // IV
        return result;
    }

    public static String invoke(String url, Object jsonParams, String token, RequestMethod requestMethod) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON); // 设置 JSON 类型
        headers.add("Accept", MediaType.APPLICATION_JSON.toString());
        if (!StringUtils.isEmpty(token)) {
            headers.add("token", token);
        }

        HttpEntity<Object> httpEntity = new HttpEntity<>(jsonParams, headers);

        RestTemplate rst = new RestTemplate();
        rst.getMessageConverters().set(1, new StringHttpMessageConverter(StandardCharsets.UTF_8));

        ResponseEntity<String> responseEntity;
        try {
            if (RequestMethod.POST.equals(requestMethod)) {
                responseEntity = rst.postForEntity(url, httpEntity, String.class);
            } else if (RequestMethod.PUT.equals(requestMethod)) {
                responseEntity = rst.exchange(url, HttpMethod.PUT, httpEntity, String.class);
            } else if (RequestMethod.DELETE.equals(requestMethod)) {
                responseEntity = rst.exchange(url, HttpMethod.DELETE, httpEntity, String.class);
            } else {
                responseEntity = rst.exchange(url, HttpMethod.GET, httpEntity, String.class);
            }
            return responseEntity.getBody();
        } catch (Exception e) {
            return e.getMessage();
        }
    }

    public static String invoke(String url, Map<String, Object> params, String token, RequestMethod requestMethod, boolean isEncrypted, String signature) {

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON); // 设置请求体为 JSON
        if (!StringUtils.isEmpty(token)) {
            headers.add("Authorization", token);
        }
        if(isEncrypted){
            headers.add("X-Data-Encrypted", "true");
        }

        if(!StringUtils.isEmpty(signature)){
            headers.add("X-Data-Signature", signature);
        }

        // 使用 JSON 字符串构建 HttpEntity
        HttpEntity<Map<String, Object>> httpEntity = new HttpEntity<>(params, headers);

        RestTemplate rst = new RestTemplate();
        ResponseEntity<String> responseEntity;
        try {
            if (RequestMethod.POST.equals(requestMethod)) {
                System.out.println(httpEntity);
                responseEntity = rst.postForEntity(url, httpEntity, String.class);
            } else if (RequestMethod.PUT.equals(requestMethod)) {
                responseEntity = rst.exchange(url, HttpMethod.PUT, httpEntity, String.class);
            } else if (RequestMethod.DELETE.equals(requestMethod)) {
                responseEntity = rst.exchange(url, HttpMethod.DELETE, httpEntity, String.class);
            } else {
                responseEntity = rst.exchange(url, HttpMethod.GET, httpEntity, String.class);
            }
        } catch (Exception e) {
            return e.getMessage();
        }

        return responseEntity.getBody();
    }
}
