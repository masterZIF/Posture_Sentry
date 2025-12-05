/**
 * Posture Pal - 前端逻辑
 * 根据姿势数据处理实时状态更新和主题切换。
 */

document.addEventListener("DOMContentLoaded", function() {
    // DOM 元素
    const dom = {
        card: document.getElementById("status-card-bg"),
        face: document.getElementById("emoji-face"),
        mainText: document.getElementById("status-text"),
        subText: document.getElementById("sub-text"),
        angle: document.getElementById("angle-value")
    };

    const REFRESH_RATE = 500; // 毫秒

    function syncPostureStatus() {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                dom.angle.textContent = data.angle + "°";

                // 协议: 后端在姿势不良时返回 "Warning: ..." 字符串。
                // 我们将这个简单的字符串协议映射到 UI 主题。
                const isWarning = data.status && data.status.includes("Warning");
                updateTheme(isWarning);
            })
            .catch(console.error); // 忽略网络故障，避免控制台刷屏
    }

    function updateTheme(isWarning) {
        if (isWarning) {
            // 姿势不良状态
            setStyles('var(--state-bad-bg)', 'var(--state-bad-text)');
            dom.face.textContent = "🥺";
            dom.mainText.textContent = "脖子酸了吗？";
            dom.subText.textContent = "稍微抬起头，休息一下吧";
        } else {
            // 姿势良好状态
            setStyles('var(--state-good-bg)', 'var(--state-good-text)');
            dom.face.textContent = "🥰";
            dom.mainText.textContent = "坐姿很棒！";
            dom.subText.textContent = "保持这个状态，继续加油哦";
        }
    }

    function setStyles(bgColor, textColor) {
        // 如果样式匹配，则阻止不必要的重绘 (可选优化)
        if (dom.card.style.backgroundColor !== bgColor) {
            dom.card.style.backgroundColor = bgColor;
            dom.mainText.style.color = textColor;
            dom.subText.style.color = textColor;
        }
    }

    // 开始轮询
    setInterval(syncPostureStatus, REFRESH_RATE);
});