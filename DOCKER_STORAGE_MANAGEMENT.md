# Docker Storage Management Guide

## 🚨 **Current Issue**
Your C: drive space decreased from 19GB to 9GB (10GB used) while using Docker because:

1. **Docker Images** are stored on C: drive
2. **Container data** accumulates on C: drive  
3. **Build cache** consumes significant space
4. **Volumes and logs** grow over time

## 💡 **Solutions**

### **Immediate Space Recovery**
```powershell
# Clean up Docker (frees ~3-5GB)
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove build cache
docker builder prune -a
```

### **Move Docker to D: Drive**

#### **Option 1: GUI Method (Easiest)**
1. Open **Docker Desktop**
2. Go to **Settings** ⚙️
3. Navigate to **Resources → Advanced**
4. Change **Disk image location** from:
   - `C:\Users\[username]\AppData\Local\Docker\wsl\data`
   - To: `D:\Docker\wsl\data`
5. Click **Apply & Restart**

#### **Option 2: PowerShell Script (Automated)**
```powershell
# Run the migration script
.\move-docker-to-d-drive.ps1
```

#### **Option 3: Manual WSL2 Migration**
```powershell
# 1. Stop Docker Desktop
# 2. Stop WSL2
wsl --shutdown

# 3. Create D: drive directory
New-Item -ItemType Directory -Path "D:\Docker\wsl" -Force

# 4. Export current Docker data
wsl --export docker-desktop-data "D:\Docker\docker-desktop-data.tar"

# 5. Unregister old distribution
wsl --unregister docker-desktop-data

# 6. Import to D: drive
wsl --import docker-desktop-data "D:\Docker\wsl\docker-desktop-data" "D:\Docker\docker-desktop-data.tar"

# 7. Start Docker Desktop and update settings
```

## 🔧 **Project-Specific Solutions**

### **Update Docker Compose for D: Drive**
```yaml
# In docker-compose.yml, add volume mappings to D: drive
volumes:
  - ./backend/data:/app/data
  - ./backend/uploads:/app/uploads  
  - ./backend/chroma_db:/app/chroma_db
  - D:/Docker/volumes/ats-data:/app/persistent-data
```

### **Environment Variables for D: Drive**
```bash
# Add to .env file
DOCKER_DATA_ROOT=D:/Docker/volumes
UPLOAD_DIR=D:/Docker/volumes/uploads
CHROMA_PERSIST_DIRECTORY=D:/Docker/volumes/chroma_db
```

## 📊 **Monitor Disk Usage**

### **Check Docker Space Usage**
```powershell
# Check Docker system disk usage
docker system df

# Check specific container sizes
docker ps -s

# Monitor build cache
docker builder df
```

### **Regular Maintenance**
```powershell
# Weekly cleanup (add to scheduled task)
docker system prune -f
docker image prune -f
docker builder prune -f
```

## 🛠 **Troubleshooting**

### **If Migration Fails**
1. **Ensure Docker Desktop is stopped completely**
2. **Check WSL2 status**: `wsl --list -v`
3. **Verify D: drive has enough space** (at least 20GB free)
4. **Run as Administrator** if permission issues occur

### **Rollback if Needed**
```powershell
# If something goes wrong, restore from backup
wsl --unregister docker-desktop-data
# Reinstall Docker Desktop (will recreate on C: drive)
```

## 📈 **Space Optimization Tips**

1. **Use .dockerignore files** (already created)
2. **Multi-stage builds** (already implemented)
3. **Regular cleanup** with system prune
4. **Limit log file sizes** in docker-compose.yml
5. **Use specific image tags** instead of 'latest'

## 💾 **Expected Space Savings**
- **Moving to D: drive**: All future Docker data on D:
- **System cleanup**: 3-5GB immediate recovery  
- **Regular maintenance**: Prevents accumulation
- **Optimized builds**: Smaller image sizes

After migration, your C: drive usage should return close to the original 19GB free space!