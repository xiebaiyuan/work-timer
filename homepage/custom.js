/************************************
 **     Timer helper functions     **
 ************************************/

// 日志控制变量
const DEBUG_MODE = false;

// 日志函数
function log(...args) {
  if (DEBUG_MODE) {
    console.log(...args);
  }
}

// 时间数据缓存
let timerData = {
  startTime: null,        // 开始时间戳
  lastSyncTime: null,     // 上次同步时间
  currentDisplay: null,   // 当前显示的时间字符串
  elapsedAtSync: null,    // 同步时获取的已计时时间
  isCheckedOut: false,    // 是否已下班
  checkoutTime: null      // 下班时间
};

// 格式化时间为 HH:MM:SS
function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

// 从服务器同步数据
function syncFromServer() {
  const url = 'https://xxxx.com/query?device_name=%E8%83%96';
  
  log('从服务器同步数据...');
  return fetch(url)
    .then((res) => {
      if (!res.ok) {
        throw new Error(`HTTP 错误: ${res.status}`);
      }
      return res.json();
    })
    .then((data) => {
      // 检查是否有真实的时间数据
      if (data?.message === 'No records for today') {
        // 如果今天没有记录，重置所有状态
        timerData.elapsedAtSync = null;
        timerData.lastSyncTime = null;
        timerData.isCheckedOut = false;
        timerData.checkoutTime = null;
        log('服务器返回今天无记录');
      } else if (data?.elapsed_time) {
        // 使用后端返回的下班状态
        timerData.isCheckedOut = data.is_off_work || false;
        timerData.elapsedAtSync = data.elapsed_time;
        timerData.lastSyncTime = Date.now();
        
        log('后端返回数据:', {
          elapsed_time: data.elapsed_time,
          is_off_work: data.is_off_work,
          last_timestamp: data.last_timestamp
        });
        
        if (timerData.isCheckedOut && data.last_timestamp) {
          // 如果已下班，提取下班时间
          timerData.checkoutTime = new Date(data.last_timestamp).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
          });
          log('检测到已下班，时间:', timerData.checkoutTime);
        } else {
          // 未下班，清空下班时间
          timerData.checkoutTime = null;
          log('服务器数据同步成功，继续计时:', timerData);
        }
      } else {
        // 其他情况视为没有有效数据
        timerData.elapsedAtSync = null;
        timerData.lastSyncTime = null;
        timerData.isCheckedOut = false;
        timerData.checkoutTime = null;
        log('服务器返回的数据无效');
      }
      return timerData.elapsedAtSync;
    })
    .catch((err) => {
      console.error('服务器数据同步失败:', err.message);
      return null;
    });
}

// 解析时间字符串为秒数
function parseTimeString(timeStr) {
  if (!timeStr) return 0;
  
  let totalSeconds = 0;
  
  // 处理包含天数的格式，如 "1 day, 2:30:45" 或 "2 days, 1:15:30"
  if (timeStr.includes('day')) {
    const parts = timeStr.split(', ');
    const dayPart = parts[0];
    const timePart = parts[1];
    
    // 提取天数
    const dayMatch = dayPart.match(/(\d+)\s+days?/);
    if (dayMatch) {
      totalSeconds += parseInt(dayMatch[1]) * 24 * 3600;
    }
    
    // 解析时间部分
    if (timePart && timePart.includes(':')) {
      const [hours, minutes, seconds] = timePart.split(':').map(Number);
      totalSeconds += hours * 3600 + minutes * 60 + seconds;
    }
  } else if (timeStr.includes(':')) {
    // 处理普通时间格式，如 "9:38:14"
    const parts = timeStr.split(':');
    if (parts.length === 3) {
      const [hours, minutes, seconds] = parts.map(Number);
      totalSeconds = hours * 3600 + minutes * 60 + seconds;
    }
  }
  
  return totalSeconds;
}

// 计算当前经过的时间
function calculateCurrentTime() {
  if (!timerData.lastSyncTime || !timerData.elapsedAtSync) {
    return null; // 返回null表示未获取到时间数据
  }
  
  // 如果已经下班，不再继续计时，返回下班时的时间
  if (timerData.isCheckedOut) {
    return timerData.elapsedAtSync;
  }
  
  // 解析上次同步时的已计时时间
  let elapsedSecondsAtSync;
  try {
    elapsedSecondsAtSync = parseTimeString(timerData.elapsedAtSync);
    log('解析时间:', timerData.elapsedAtSync, '-> 秒数:', elapsedSecondsAtSync);
  } catch (error) {
    log('时间解析错误:', error, '原始值:', timerData.elapsedAtSync);
    return timerData.elapsedAtSync; // 直接返回原始值
  }
  
  // 计算从同步到现在经过的额外秒数
  const additionalSeconds = Math.floor((Date.now() - timerData.lastSyncTime) / 1000);
  
  // 计算总经过时间
  const totalElapsedSeconds = elapsedSecondsAtSync + additionalSeconds;
  
  // 格式化为 HH:MM:SS
  return formatTime(totalElapsedSeconds);
}

// 更新显示
function updateDisplay() {
  const currentTime = calculateCurrentTime();
  
  // 确定要显示的文本
  let displayText;
  if (currentTime === null) {
    displayText = '今日未签到';
  } else if (timerData.isCheckedOut) {
    displayText = `已下班 (${timerData.checkoutTime}) 共工作：${currentTime}`;
  } else {
    displayText = `今天已工作：${currentTime}`;
  }
  
  // 如果显示内容没变，就不更新DOM
  if (displayText === timerData.currentDisplay) {
    return;
  }
  
  timerData.currentDisplay = displayText;
  
  const targets = document.querySelectorAll('#Timer .service-description');
  if (targets.length > 0) {
    for (const el of targets) {
      el.textContent = displayText;
    }
    log('显示已更新:', displayText);
  }
}

/************************************
 **     Auto refresh functions     **
 ************************************/

let displayIntervalId = null;  // 显示更新计时器
let syncIntervalId = null;     // 同步数据计时器

function startAutoRefresh() {
  // 先清除可能存在的旧定时器
  stopAutoRefresh();
  
  // 立即同步一次数据
  syncFromServer().then(() => {
    updateDisplay(); // 先更新一次显示
    
    // 设置数据同步计时器（每分钟同步一次）
    syncIntervalId = setInterval(() => {
      syncFromServer().then(() => {
        updateDisplay();
        
        // 根据状态调整显示更新频率
        if (timerData.isCheckedOut && displayIntervalId) {
          // 如果检测到已下班，停止持续计时
          clearInterval(displayIntervalId);
          displayIntervalId = null;
          log('检测到下班状态，停止持续计时');
        } else if (!timerData.isCheckedOut && !displayIntervalId) {
          // 如果检测到重新上班，重新开始持续计时
          displayIntervalId = setInterval(updateDisplay, 1000);
          log('检测到重新上班，开始持续计时');
        }
      });
    }, 60000);
    
    // 如果没有下班，设置1秒更新一次显示的计时器
    if (!timerData.isCheckedOut) {
      displayIntervalId = setInterval(updateDisplay, 1000);
      log('已启动自动刷新（显示每秒更新，数据每分钟同步）');
    } else {
      log('已下班，只同步数据不持续计时');
    }
  });
}

function stopAutoRefresh() {
  if (displayIntervalId) {
    clearInterval(displayIntervalId);
    displayIntervalId = null;
  }
  
  if (syncIntervalId) {
    clearInterval(syncIntervalId);
    syncIntervalId = null;
  }
  
  log('已停止自动刷新');
}

/************************************
 **              MAIN              **
 ************************************/

// 等待 DOM 完全加载
document.addEventListener('DOMContentLoaded', () => {
  log('DOM 已加载，准备执行注入');
  
  // 监听 DOM 变化
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === 'childList' || mutation.type === 'subtree') {
        const targets = document.querySelectorAll('#Timer');
        if (targets.length > 0) {
          log('检测到目标元素变化');
          // 如果元素可见，确保自动刷新已开启
          if ((!displayIntervalId || !syncIntervalId) && document.visibilityState === 'visible') {
            startAutoRefresh();
          }
        } else if (displayIntervalId || syncIntervalId) {
          // 如果元素不存在，停止自动刷新以节省资源
          stopAutoRefresh();
        }
      }
    }
  });
  
  // 监听整个文档变化
  observer.observe(document.body, { 
    childList: true, 
    subtree: true 
  });
  
  // tab 切换后重新检查
  const tabsElement = document.getElementById('tabs');
  if (tabsElement) {
    tabsElement.addEventListener('click', () => {
      log('检测到 tab 点击');
      // 延迟确保 DOM 已更新
      setTimeout(() => {
        // 检查元素是否存在，决定是否启动自动刷新
        const targets = document.querySelectorAll('#Timer');
        if (targets.length > 0) {
          startAutoRefresh();
        } else {
          stopAutoRefresh();
        }
      }, 300);
    });
  } else {
    console.warn('未找到 tabs 元素');
  }
  
  // 页面可见性变化时控制自动刷新
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      // 页面可见时，如果元素存在则启动自动刷新
      const targets = document.querySelectorAll('#Timer');
      if (targets.length > 0) {
        startAutoRefresh();
      }
    } else {
      // 页面不可见时停止自动刷新以节省资源
      stopAutoRefresh();
    }
  });
  
  // 初始检查
  const targets = document.querySelectorAll('#Timer');
  if (targets.length > 0) {
    startAutoRefresh();
  }
});

// 如果页面已经加载完毕，立即执行
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  log('页面已加载，立即执行检查');
  const targets = document.querySelectorAll('#Timer');
  if (targets.length > 0) {
    startAutoRefresh();
  }
}