import Cocoa

class DetailsViewController: NSViewController {
    
    var scrollView: NSScrollView!
    var textView: NSTextView!
    var jsonDataToDisplay: [String: Any]? // 保存传入的 JSON 数据
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // 创建滚动视图
        scrollView = NSScrollView()
        scrollView.hasVerticalScroller = true
        scrollView.hasHorizontalScroller = false
        scrollView.translatesAutoresizingMaskIntoConstraints = false  // 关闭自动调整布局
        scrollView.wantsLayer = true
        scrollView.layer?.borderColor = NSColor.blue.cgColor
        scrollView.layer?.borderWidth = 1.0
        
        // 创建 NSTextView，并将其添加到滚动视图中
        textView = NSTextView()
        textView.isEditable = false
        textView.isVerticallyResizable = true
        textView.isHorizontallyResizable = false
        textView.translatesAutoresizingMaskIntoConstraints = false  // 关闭自动调整布局
        textView.textContainer?.containerSize = NSSize(width: scrollView.contentSize.width, height: CGFloat.greatestFiniteMagnitude)
        textView.textContainer?.widthTracksTextView = true
        textView.backgroundColor = NSColor.white
        textView.textColor = NSColor.black
        textView.wantsLayer = true
        textView.layer?.borderColor = NSColor.green.cgColor
        textView.layer?.borderWidth = 1.0
        // 将 NSTextView 添加到 NSScrollView 的 contentView 中
        scrollView.documentView = textView
        
        // 将滚动视图添加到视图中
        self.view.addSubview(scrollView)
        
        // 添加约束，使滚动视图填满整个视图控制器的视图
        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: self.view.topAnchor),
            scrollView.bottomAnchor.constraint(equalTo: self.view.bottomAnchor),
            scrollView.leadingAnchor.constraint(equalTo: self.view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: self.view.trailingAnchor)
        ])
        
        // 在视图加载完成后，更新内容
        updateTextViewContent()
    }
    
    // 更新 NSTextView 的内容
    func updateTextViewContent() {
        // 确保 textView 已经被初始化
        guard let textView = textView else {
            print("textView 尚未初始化")
            return
        }

        if let jsonData = jsonDataToDisplay {
            print("jsonDataToDisplay 有数据: \(jsonData)")
            if let jsonDataString = jsonToString(jsonData) {
                print("jsonDataString: \(jsonDataString)")
                textView.string = jsonDataString
            } else {
                print("无法将 jsonData 转换为字符串")
                textView.string = "无法解析 JSON 数据"
            }
        } else {
            print("jsonDataToDisplay 为 nil")
            textView.string = "无数据"
        }
    }
    
    // 更新 Details 界面显示 JSON 数据
    func updateDetails(jsonData: [String: Any]?) {
        // 保存传入的 JSON 数据
        jsonDataToDisplay = jsonData
        
        // 如果视图已加载，更新内容
        if isViewLoaded {
            updateTextViewContent()
        }
    }
    
    // 将 JSON 转换为字符串格式
    func jsonToString(_ json: [String: Any]) -> String? {
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: json, options: .prettyPrinted)
            return String(data: jsonData, encoding: .utf8)
        } catch {
            print("JSON 转换为字符串失败: \(error.localizedDescription)")
            return nil
        }
    }
}
