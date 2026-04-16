#!/bin/bash
# =========================================================================
# 脚本名称: run_ms_swift_training.sh
# 作用: 自动在远程 GPU 服务器上配置 Miniconda 环境并运行 ms-swift 训练任务
# 使用方式: 
#   ./run_ms_swift_training.sh <JOB_ID> <PYTHON_ENV_NAME> <SWIFT_SFT_ARGS...>
# 示例:
#   ./run_ms_swift_training.sh job-12345 swift_env --model_type qwen1half-7b-chat --dataset data.jsonl
# =========================================================================

# 开启严格错误检测模式 (可选，遇到错误退出)
set -e

JOB_ID=$1
ENV_NAME=$2
# 将前两个参数移出，剩下的就是纯粹的 swift sft 参数
shift 2

# ---------------------------------------------------------
# 1. 查找并初始化 Miniconda/Anaconda
# ---------------------------------------------------------
echo "[INFO] 正在初始化 Conda 环境..."
# 尝试猜测常见的 conda 安装路径
CONDA_PATHS=(
    "$HOME/miniconda3"
    "$HOME/anaconda3"
    "/opt/miniconda3"
    "/opt/anaconda3"
    "/usr/local/miniconda3"
)

CONDA_BASE=""
# 如果 conda 已经在环境变量中，直接获取
if command -v conda &> /dev/null; then
    CONDA_BASE=$(conda info --base)
else
    for p in "${CONDA_PATHS[@]}"; do
        if [ -d "$p" ]; then
            CONDA_BASE=$p
            break
        fi
    done
fi

if [ -z "$CONDA_BASE" ]; then
    echo "[ERROR] 找不到 Miniconda 或 Anaconda 安装路径。请检查基础环境配置。"
    exit 1
fi

source "$CONDA_BASE/etc/profile.d/conda.sh"

# ---------------------------------------------------------
# 2. 创建或激活指定的 Python 虚拟环境
# ---------------------------------------------------------
if conda info --envs | awk '{print $1}' | grep -Fxq "$ENV_NAME"; then
    echo "[INFO] Conda 虚拟环境 '$ENV_NAME' 已存在，直接激活。"
else
    echo "[INFO] Conda 虚拟环境 '$ENV_NAME' 不存在，正在创建 (Python 3.10)..."
    conda create -n "$ENV_NAME" python=3.10 -y
fi

echo "[INFO] 激活环境: $ENV_NAME"
conda activate "$ENV_NAME"

# ---------------------------------------------------------
# 3. 检查并安装 ms-swift 及其依赖
# ---------------------------------------------------------
echo "[INFO] 检查 ms-swift 和依赖环境..."

# 检查是否安装了 ms-swift，如果没安装，则安装包含 LLM 的版本
if ! python -c "import swift" &> /dev/null; then
    echo "[INFO] 未检测到 ms-swift，正在安装..."
    # 推荐使用国内镜像加速
    pip install "ms-swift[llm]" -U -i https://mirrors.aliyun.com/pypi/simple/
    
    # 针对需要 flash-attn 的大模型可以视情况补充安装
    # pip install flash-attn --no-build-isolation
else
    echo "[INFO] ms-swift 已经安装。"
fi

# ---------------------------------------------------------
# 4. 执行训练任务
# ---------------------------------------------------------
# 为每次任务生成一个独立的日志文件路径
LOG_DIR="$HOME/training_logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/${JOB_ID}_$(date +%Y%m%d%H%M%S).log"

echo "[INFO] ========================================"
echo "[INFO] 开始执行训练任务 (Job ID: $JOB_ID)"
echo "[INFO] 训练参数: $@"
echo "[INFO] 实时日志将保存至: $LOG_FILE"
echo "[INFO] ========================================"

# 关闭严格错误，为了捕获 swift 命令的退出码
set +e

# 执行 swift sft，同时将日志打印到终端和文件
# 后端可以通过 SSH 实时 tail -f 这个文件来获取进度
swift sft "$@" 2>&1 | tee "$LOG_FILE"

TRAIN_EXIT_CODE=${PIPESTATUS[0]}

# ---------------------------------------------------------
# 5. 后置处理与清理
# ---------------------------------------------------------
if [ $TRAIN_EXIT_CODE -eq 0 ]; then
    echo "[SUCCESS] 训练任务 $JOB_ID 成功完成！"
else
    echo "[ERROR] 训练任务 $JOB_ID 异常终止，退出码: $TRAIN_EXIT_CODE"
fi

# 退出环境
conda deactivate

exit $TRAIN_EXIT_CODE
