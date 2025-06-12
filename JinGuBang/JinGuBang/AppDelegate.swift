import Cocoa
import Foundation

@main
class AppDelegate: NSObject, NSApplicationDelegate, NSPopoverDelegate {
    
    var statusItem: NSStatusItem?
    var popover: NSPopover = NSPopover()
    var targetDate: Date?
    var timer: Timer?
    var jsonData: [String: Any]? // 保存请求到的 JSON 数据
    
    func applicationDidFinishLaunching(_ aNotification: Notification) {
        // 创建状态栏图标
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        
        if let button = statusItem?.button {
            button.title = "加载中..."
            button.action = #selector(togglePopover) // 点击状态栏图标时，显示或隐藏 Popover
        }
        
        // 手动初始化 DetailsViewController 并设置为 popover 的 contentViewController
        let detailsViewController = DetailsViewController()
        popover.contentViewController = detailsViewController
        popover.delegate = self // 设置 NSPopover 代理
        
        // 启动时立即执行一次API请求，并设置定时器
        fetchAPIData()
    }
    
//    @objc func togglePopover() {
//        if let button = statusItem?.button {
//            if popover.isShown {
//                popover.performClose(nil) // 如果Popover已经显示，则关闭
//            } else {
//                if let viewController = popover.contentViewController as? DetailsViewController {
//                    // 传递并更新 DetailsViewController 的 JSON 数据
//                    viewController.updateDetails(jsonData: jsonData)
//                }
//                popover.show(relativeTo: button.bounds, of: button, preferredEdge: .minY) // 显示Popover
//            }
//        }
//    }
    ////////////////////////////////////////////////////////////////
    @objc func togglePopover() {
        if let button = statusItem?.button {
            // 点击状态栏时发送请求获取最新签到时间
            fetchAPIData()
            sendNotification()
        }
    }

    func sendNotification() {
        let notification = NSUserNotification()
        notification.title = "今天打卡时间"
        
        // 设置通知的内容，展示倒计时或其他信息
        if let jsonData = jsonData, let first_timestamp = jsonData["today_first_timestamp"] as? String {
            notification.informativeText = "今天的时间戳: \(first_timestamp)"
        } else {
            notification.informativeText = "没有可用的数据"
        }
        
        // 配置通知时间
        notification.deliveryDate = Date()
        
        // 发送通知
        NSUserNotificationCenter.default.deliver(notification)
    }
    
    // NSPopoverDelegate 方法，当 Popover 失去焦点时关闭它
    func popoverDidResignKey(_ notification: Notification) {
        popover.performClose(nil) // 当 Popover 失去焦点时自动关闭
    }
    
    // 在状态栏图标被隐藏、应用失去焦点或屏幕配置变化时关闭 Popover
    @objc func closePopover() {
        if popover.isShown {
            popover.performClose(nil)
        }
    }
    
    // 停止定时器
    func stopTimer() {
        timer?.invalidate()
        timer = nil
    }
    
    // 发送网络请求获取状态并更新状态栏
    @objc func fetchAPIData() {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30.0
        configuration.waitsForConnectivity = true
        
        let session = URLSession(configuration: configuration)
        let url = URL(string: "https://timer.xiebaiyuan.com:45456/query?device_name=%E8%83%96")!
        
        let task = session.dataTask(with: url) { [weak self] data, response, error in
            guard let self = self else { return }
            if let error = error {
                print("请求失败: \(error.localizedDescription)")
                return
            }
            
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200, let data = data {
                do {
                    // 尝试将数据解析为 JSON
                    let json = try JSONSerialization.jsonObject(with: data, options: [])
                    
                    if let jsonObject = json as? [String: Any] {
                        print("提取的 JSON 数据: \(jsonObject)")
                        
                        // 保存 JSON 数据
                        self.jsonData = jsonObject
                        
                        DispatchQueue.main.async {
                            if let first_timestamp = jsonObject["today_first_timestamp"] as? String {
                                self.targetDate = self.dateFromString(first_timestamp)
                                self.stopTimer()
                                self.startTimer() // 启动定时器，定期更新状态栏时间
                            }
                        }
                    }
                } catch {
                    print("JSON 解析错误: \(error.localizedDescription)")
                }
            } else {
                print("请求失败，状态码: \((response as? HTTPURLResponse)?.statusCode ?? 0)")
            }
        }
        task.resume()
    }
    
    // 启动定时器，更新剩余时间
    func startTimer() {
        if timer == nil {
            timer = Timer.scheduledTimer(timeInterval: 1.0, target: self, selector: #selector(updateTimeDifference), userInfo: nil, repeats: true)
        }
    }
    
    // 每秒计算目标时间与当前时间的差值，并更新状态栏
    @objc func updateTimeDifference() {
        guard let targetDate = targetDate else {
            return
        }
        
        let currentDate = Date()
        let timeInterval = Int(currentDate.timeIntervalSince(targetDate)) // 获取已经过去的秒数
        
        if timeInterval >= 0 {
            let formattedTime = ""+formatTime(seconds: timeInterval)
            updateStatusBar(title: formattedTime)
        } else {
            updateStatusBar(title: "时间未到")
        }
    }
    
    // 更新状态栏的显示
    func updateStatusBar(title: String) {
        if let button = statusItem?.button {
            button.title = title
        }
    }
    
    // 将字符串转换为 Date 对象
    func dateFromString(_ dateString: String) -> Date? {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        dateFormatter.timeZone = TimeZone.current
        return dateFormatter.date(from: dateString)
    }
    
    // 格式化时间为 "xx小时 xx分钟 xx秒"
    func formatTime(seconds: Int) -> String {
        let hours = seconds / 3600
        let minutes = (seconds % 3600) / 60
        let remainingSeconds = seconds % 60
        return String(format: " %02d:%02d:%02d ", hours, minutes, remainingSeconds)
    }
}
