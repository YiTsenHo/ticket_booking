// 等待文檔加載完成
document.addEventListener('DOMContentLoaded', function() {
    // 為預訂狀態添加視覺效果
    const statusTags = document.querySelectorAll('.status-tag');
    statusTags.forEach(tag => {
        if (tag.textContent === '已預訂') {
            tag.title = '此座位已被預訂';
        } else if (tag.textContent === '可預訂') {
            tag.title = '此座位可以預訂';
        }
    });

    // 為座位標籤添加提示
    const seatTags = document.querySelectorAll('.seat-tag');
    seatTags.forEach(tag => {
        tag.title = '點擊查看詳情';
    });

    // 添加對行的高亮效果
    const rows = document.querySelectorAll('#result_list tbody tr');
    rows.forEach(row => {
        row.addEventListener('mouseover', function() {
            this.style.backgroundColor = '#f0f7ff';
        });
        
        row.addEventListener('mouseout', function() {
            this.style.backgroundColor = '';
        });
    });
    
});
