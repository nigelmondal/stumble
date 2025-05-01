Stumbl - README  

Project Overview  

Stumbl is a web platform that connects students for academic support, project collaboration, and competition preparation. Key features include Personalized Profiles, a Matchmaking Interface, Centralized Communication Tools, and an Integrated Calendar.  

-----------------------------------------------------------------------------------------------------------------------------------------------

Requirements  

Hardware  
Processor: Intel Core i3 or higher  
RAM: 4GB or more  
Storage: Minimum 10GB free space  
Internet Connection: Required  

Software  
Operating System: Windows 10/11, macOS, or Linux  
Backend: Python 3.x, Flask, MySQL Server  
Frontend: HTML, CSS, JavaScript  
Tools: VS Code (or any code editor), MySQL Workbench  

-----------------------------------------------------------------------------------------------------------------------------------------------

Installation & Setup  

1. Clone the Repository  

git clone https://github.com/your-repo/stumbl.git  
cd stumbl  

2. Install Dependencies  

pip install -r requirements.txt  

3. Set Up MySQL Database  

Open MySQL Workbench or command line and run:  

CREATE DATABASE stumble;  
USE stumble;  

CREATE TABLE user (  
    user_id INT AUTO_INCREMENT PRIMARY KEY,  
    full_name VARCHAR(255) NOT NULL,  
    email VARCHAR(255) NOT NULL UNIQUE,  
    password VARCHAR(255) NOT NULL,  
    gender VARCHAR(6),  
    age INT,  
    bio TEXT,  
    strengths TEXT,  
    weaknesses TEXT,  
    collab_count INT DEFAULT 0  
);  

CREATE TABLE meetings (  
    meeting_id INT AUTO_INCREMENT PRIMARY KEY,  
    user_id INT NOT NULL,  
    buddy_id INT NOT NULL,  
    meeting_date DATE NOT NULL,  
    meeting_time TIME NOT NULL,  
    description TEXT NOT NULL,  
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,  
    FOREIGN KEY (buddy_id) REFERENCES user(user_id) ON DELETE CASCADE  
);  

4. Import Dummy Data  

The dataset is included in the zip folder. To insert data into the user table, import the provided dataset using MySQL Workbench or command line:  

mysql -u your_username -p stumble < dummy_dataset.sql  

5. Configure Database Connection  

Update config.py with your credentials:  

DB_HOST = 'localhost'  
DB_USER = 'your_username'  
DB_PASSWORD = 'your_password'  
DB_NAME = 'stumble'  

6. Run the Server  

python app.py  

Once started, open the IP address displayed in the terminal (e.g., http://127.0.0.1:5000/).  

-----------------------------------------------------------------------------------------------------------------------------------------------

Usage Instructions  

1. Open VS Code and navigate to the Stumbl folder.  
2. Open the terminal and start the backend:  python app.py  
3. Click the IP address provided in the terminal.  
4. Sign up and log in to create your profile.  
5. Find study partners via the matchmaking interface.  
6. Communicate using the chat feature.  
7. Schedule study sessions using the calendar.  

-----------------------------------------------------------------------------------------------------------------------------------------------

Troubleshooting  

Database connection issues? Ensure MySQL is running and credentials in config.py are correct.  
Module errors? Run pip install -r requirements.txt.  
Frontend issues? Ensure JavaScript is enabled in your browser.  

-----------------------------------------------------------------------------------------------------------------------------------------------

Additional Resources  

PPT: Project presentation  
Zipped Folder: Includes .exe file, dataset, and sample data  
Video Recording: Demonstration of platform functionality  

-----------------------------------------------------------------------------------------------------------------------------------------------

Contributors  

Apanvi Srivastava (2240250)  
Twinkle Dhingra (2240234)  
Nigel Mondal (2240224)  
