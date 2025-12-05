/**
 * POSTURE SENTRY // 终端控制器
 * 管理仪表盘数据可视化和系统日志记录。
 */

document.addEventListener("DOMContentLoaded", function() {
    const ui = {
        status: document.getElementById("posture-indicator"),
        angleVal: document.getElementById("angle-value"),
        angleBar: document.getElementById("angle-bar"),
        logList: document.querySelector(".log-list"),
        cpu: document.querySelector(".random-change")
    };
    
    // 配置: 后端状态字符串的视觉映射
    const STATUS_MAP = {
        "Normal": { 
            color: "#00ff41", 
            text: "NORMAL // 正常", 
            alert: false 
        },
        "Warning: Slouching!": { 
            color: "#ff3333", 
            text: "WARNING // 驼背", 
            alert: true 
        }
    };

    const MAX_LOGS = 8;
    let lastKnownStatus = "";

    // --- 核心逻辑: 数据同步 ---
    
    function fetchTelemetry() {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                const config = STATUS_MAP[data.status] || STATUS_MAP["Normal"];
                
                renderStatus(config);
                renderMetrics(data.angle, config.color);
                checkAlerts(data, config);
            })
            .catch(err => {
                // 仅在调试模式或首次失败时记录网络错误
                // console.warn("Connection lost...", err); 
            });
    }

    function renderStatus(config) {
        ui.status.innerText = config.text;
        ui.status.style.color = config.color;
        
        // 仅在警告时添加发光效果以吸引注意力
        const shadow = config.alert ? `0 0 15px ${config.color}` : 'none';
        ui.status.style.textShadow = shadow;
        ui.status.style.borderColor = config.alert ? config.color : "transparent";
    }

    function renderMetrics(angle, color) {
        ui.angleVal.innerText = angle + "°";
        
        // 角度归一化以用于进度条 (假设范围为 100° ~ 180°)
        // 低于 100 的值将被剪裁为 0
        const percentage = Math.max(0, Math.min(100, (angle - 100) / 0.8));
        
        ui.angleBar.style.width = percentage + "%";
        ui.angleBar.style.backgroundColor = color;
    }

    function checkAlerts(data, config) {
        // 仅在状态变化时记录日志，以防止日志板刷屏
        if (data.status !== lastKnownStatus && config.alert) {
            pushLog(`[ALERT] Posture integrity critical: ${data.angle}°`, "#ff3333");
        }
        lastKnownStatus = data.status;
    }

    function pushLog(msg, color) {
        const li = document.createElement("li");
        li.innerHTML = `<span style="color:${color || '#888'}">> ${msg}</span>`;
        
        ui.logList.prepend(li);
        
        // 保持固定的日志大小
        if (ui.logList.children.length > MAX_LOGS) {
            ui.logList.removeChild(ui.logList.lastChild);
        }
    }

    // --- 视觉效果: 模拟循环 ---
    // 与网络请求解耦，确保 UI 流畅性
    
    function simulateSystemLoad() {
        // 随机 CPU 波动效果
        if(Math.random() > 0.6) {
            const load = Math.floor(Math.random() * 30 + 10);
            ui.cpu.innerText = load + "%";
        }
    }

    // 初始化循环
    setInterval(fetchTelemetry, 500);    // 每 500 毫秒同步一次网络数据
    setInterval(simulateSystemLoad, 200); // 每 200 毫秒进行一次 UI 动画
});