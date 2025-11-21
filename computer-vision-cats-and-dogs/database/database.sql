CREATE TABLE Feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,            
    predicted_class TEXT,               
    status TEXT,                        
    inference_time_ms INTEGER,          
    succes INTEGER                      
);
