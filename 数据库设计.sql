#数据库建好了
#用户名:mao 密码:Open@12345


CREATE DATABASE IF NOT EXISTS learn_assistant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE learn_assistant;

-- ========================
-- 1. 用户表 (users)
-- ========================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) COMMENT '备用密码登录',
    face_encoding TEXT COMMENT '人脸特征编码（npy文件路径）',
    face_image_path VARCHAR(500) COMMENT '注册时的人脸照片路径',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

-- ========================
-- 2. 文档表 (documents)
-- ========================
CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '文档ID',
    filename VARCHAR(255) NOT NULL COMMENT '文件原始名称',
    file_type VARCHAR(20) NOT NULL COMMENT 'pdf / docx / txt / md / ppt / json',
    file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径',
    file_size INT COMMENT '文件大小(字节)',
    chunk_count INT DEFAULT 0 COMMENT '分块数量',
    user_id INT COMMENT '上传用户ID',
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

-- ========================
-- 3. 课程章节表 (chapters)
-- ========================
CREATE TABLE chapters (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '章节ID',
    parent_id INT COMMENT '父章节(章)，NULL=顶级章',
    title VARCHAR(255) NOT NULL COMMENT '章节标题',
    level INT NOT NULL DEFAULT 1 COMMENT '1=章, 2=节',
    sort_order INT DEFAULT 0 COMMENT '排序序号',
    content TEXT COMMENT 'LLM生成的章节学习内容',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (parent_id) REFERENCES chapters (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

-- ========================
-- 4. 学习进度表 (progress)
-- ========================
CREATE TABLE progress (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '进度ID',
    user_id INT NOT NULL COMMENT '用户ID',
    chapter_id INT NOT NULL COMMENT '章节ID',
    status VARCHAR(20) DEFAULT 'not_started' COMMENT 'not_started / learning / completed',
    started_at DATETIME COMMENT '开始学习时间',
    completed_at DATETIME COMMENT '完成时间',
    UNIQUE KEY uk_user_chapter (user_id, chapter_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

-- ========================
-- 5. 题目表 (questions)
-- ========================
CREATE TABLE questions (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '题目ID',
    chapter_id INT COMMENT '所属章节ID',
    type VARCHAR(20) NOT NULL COMMENT 'single_choice / true_false',
    difficulty VARCHAR(10) DEFAULT 'medium' COMMENT 'easy / medium / hard',
    stem TEXT NOT NULL COMMENT '题干',
    options JSON NOT NULL COMMENT '选项（MySQL JSON类型）',
    answer VARCHAR(255) NOT NULL COMMENT '正确答案',
    explanation TEXT COMMENT '解析',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

-- ========================
-- 6. 考试记录表 (exams)
-- ========================
CREATE TABLE exams (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '考试记录ID',
    user_id INT NOT NULL COMMENT '用户ID',
    chapter_id INT COMMENT '考试章节ID（NULL=综合考试）',
    total_score DECIMAL(5, 1) NOT NULL COMMENT '总分',
    score DECIMAL(5, 1) NOT NULL COMMENT '实际得分',
    time_limit INT COMMENT '时间限制(秒)',
    time_used INT COMMENT '实际用时(秒)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '考试时间',
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

-- ========================
-- 7. 答题明细表 (exam_details)
-- ========================
CREATE TABLE exam_details (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '答题明细ID',
    exam_id INT NOT NULL COMMENT '考试记录ID',
    question_id INT NOT NULL COMMENT '题目ID',
    user_answer VARCHAR(255) COMMENT '用户答案',
    is_correct TINYINT(1) COMMENT '是否正确（0=错误, 1=正确）',
    score DECIMAL(4, 1) COMMENT '本题得分',
    FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

-- ========================
-- 8. 错题本表 (wrong_book)
-- ========================
CREATE TABLE wrong_book (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '错题记录ID',
    user_id INT NOT NULL COMMENT '用户ID',
    question_id INT NOT NULL COMMENT '题目ID',
    chapter_id INT COMMENT '所属章节ID',
    exam_id INT COMMENT '来源考试ID',
    wrong_count INT DEFAULT 1 COMMENT '错误次数',
    correct_count INT DEFAULT 0 COMMENT '后续答对次数',
    last_wrong_at DATETIME COMMENT '最近错误时间',
    last_practiced_at DATETIME COMMENT '最近练习时间',
    UNIQUE KEY uk_user_question (user_id, question_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE SET NULL,
    FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;