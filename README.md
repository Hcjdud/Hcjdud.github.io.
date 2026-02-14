<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Telegram Mini Shop</title>
    <!-- Подключаем Telegram SDK -->
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            transition: background 0.3s;
        }
        
        /* Тёмная тема Telegram */
        body.dark-theme {
            background: linear-gradient(135deg, #2c3e50 0%, #1e1e2f 100%);
        }
        
        #app {
            max-width: 500px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Стили для уведомлений */
        .notification {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 12px 24px;
            border-radius: 30px;
            font-size: 14px;
            z-index: 10000;
            animation: slideDown 0.3s ease;
            max-width: 90%;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .notification.success {
            background: rgba(76, 175, 80, 0.9);
        }
        
        .notification.error {
            background: rgba(244, 67, 54, 0.9);
        }
        
        @keyframes slideDown {
            from {
                top: -50px;
                opacity: 0;
            }
            to {
                top: 20px;
                opacity: 1;
            }
        }
        
        /* Кнопки и инпуты */
        button, input {
            font-family: inherit;
        }
        
        input:focus {
            outline: 2px solid rgba(255,255,255,0.5);
        }
    </style>
</head>
<body>
    <div id="app"></div>

    <script>
        // ============================================
        // 0. ИНИЦИАЛИЗАЦИЯ TELEGRAM SDK
        // ============================================
        const tg = window.Telegram?.WebApp;
        
        if (!tg) {
            alert("⚠️ Это приложение должно работать внутри Telegram!");
        } else {
            tg.ready();
            tg.expand();
            
            // Применяем тему Telegram
            if (tg.colorScheme === 'dark') {
                document.body.classList.add('dark-theme');
            }
            
            // Получаем данные пользователя
            const user = tg.initDataUnsafe?.user;
            console.log("📱 Данные Telegram:", user);
        }
        
        // ============================================
        // 1. БАЗА ДАННЫХ
        // ============================================
        const MiniShopDB = {
            // Текущий пользователь (из Telegram)
            currentUser: user ? {
                id: user.id,
                username: user.username || `${user.first_name} ${user.last_name || ''}`.trim(),
                telegramId: user.id,
                firstName: user.first_name,
                lastName: user.last_name,
                balance: 500,
                isAdmin: false // Обычный пользователь не админ
            } : null,
            
            // Администратор (логин: aaaaf, пароль: 26424)
            admin: {
                login: 'aaaaf',
                password: '26424',
                id: 'admin_001',
                username: 'Administrator',
                balance: 999999,
                isAdmin: true
            },
            
            // Все пользователи
            users: [],
            
            // Товары
            products: [
                { id: 101, name: "📱 Виртуальный номер", price: 150, category: "services", stock: 50, description: "Номер для регистрации Telegram" },
                { id: 102, name: "💎 Premium аккаунт", price: 500, category: "accounts", stock: 10, description: "Аккаунт с историей" },
                { id: 103, name: "🚀 Ускоритель", price: 300, category: "services", stock: 100, description: "Повышение скорости" },
                { id: 104, name: "🛡️ Защита", price: 250, category: "services", stock: 25, description: "Анти-бан защита" },
                { id: 105, name: "🌟 VIP подписка", price: 1000, category: "subscriptions", stock: 5, description: "30 дней привилегий" }
            ],
            
            // Корзина
            cart: [],
            
            // Заказы
            orders: [],
            
            // Следующий ID для заказа
            nextOrderId: 1,
            
            // Состояние приложения
            isAdminMode: false // Режим администратора выключен по умолчанию
        };
        
        // Добавляем Telegram-пользователя в список
        if (user && !MiniShopDB.users.find(u => u.telegramId === user.id)) {
            MiniShopDB.users.push(MiniShopDB.currentUser);
        }
        
        // Загружаем сохранения
        try {
            const savedCart = localStorage.getItem('shop_cart_' + user?.id);
            if (savedCart) MiniShopDB.cart = JSON.parse(savedCart);
            
            const savedOrders = localStorage.getItem('shop_orders_' + user?.id);
            if (savedOrders) {
                MiniShopDB.orders = JSON.parse(savedOrders);
                MiniShopDB.nextOrderId = Math.max(...MiniShopDB.orders.map(o => o.id), 0) + 1;
            }
        } catch (e) {
            console.log("Ошибка загрузки сохранений:", e);
        }
        
        // ============================================
        // 2. УТИЛИТЫ
        // ============================================
        function showNotification(message, type = 'info') {
            const notif = document.createElement('div');
            notif.className = `notification ${type}`;
            notif.textContent = message;
            document.body.appendChild(notif);
            
            setTimeout(() => {
                notif.style.animation = 'slideDown 0.3s reverse';
                setTimeout(() => notif.remove(), 300);
            }, 2000);
        }
        
        // ============================================
        // 3. ЯДРО МАГАЗИНА
        // ============================================
        const ShopCore = {
            // Вход администратора
            adminLogin: function(login, password) {
                if (login === MiniShopDB.admin.login && password === MiniShopDB.admin.password) {
                    MiniShopDB.isAdminMode = true;
                    MiniShopDB.currentUser = MiniShopDB.admin;
                    return { success: true, message: "✅ Добро пожаловать, администратор!" };
                }
                return { success: false, message: "❌ Неверные данные администратора" };
            },
            
            // Выход из режима администратора
            adminLogout: function() {
                MiniShopDB.isAdminMode = false;
                MiniShopDB.currentUser = user ? {
                    id: user.id,
                    username: user.username || `${user.first_name} ${user.last_name || ''}`.trim(),
                    telegramId: user.id,
                    firstName: user.first_name,
                    lastName: user.last_name,
                    balance: 500,
                    isAdmin: false
                } : null;
                return { success: true, message: "👋 Выход из режима администратора" };
            },
            
            // Сохранение
            saveCart: function() {
                if (user && !MiniShopDB.isAdminMode) {
                    localStorage.setItem('shop_cart_' + user.id, JSON.stringify(MiniShopDB.cart));
                }
            },
            
            saveOrders: function() {
                if (user && !MiniShopDB.isAdminMode) {
                    localStorage.setItem('shop_orders_' + user.id, JSON.stringify(MiniShopDB.orders));
                }
            },
            
            // Добавление товара (только для админа)
            addProduct: function(productData) {
                if (!MiniShopDB.isAdminMode) {
                    return { success: false, message: "❌ Только для администратора" };
                }
                
                const newId = Math.max(...MiniShopDB.products.map(p => p.id), 0) + 1;
                const product = {
                    id: newId,
                    name: productData.name,
                    price: parseInt(productData.price),
                    category: productData.category,
                    stock: parseInt(productData.stock),
                    description: productData.description
                };
                
                MiniShopDB.products.push(product);
                return { success: true, message: `✅ Товар "${product.name}" добавлен`, product: product };
            },
            
            // Удаление товара (только для админа)
            deleteProduct: function(productId) {
                if (!MiniShopDB.isAdminMode) {
                    return { success: false, message: "❌ Только для администратора" };
                }
                
                const index = MiniShopDB.products.findIndex(p => p.id === productId);
                if (index !== -1) {
                    const deleted = MiniShopDB.products.splice(index, 1)[0];
                    return { success: true, message: `✅ Товар "${deleted.name}" удалён` };
                }
                return { success: false, message: "❌ Товар не найден" };
            },
            
            // Редактирование товара (только для админа)
            editProduct: function(productId, updates) {
                if (!MiniShopDB.isAdminMode) {
                    return { success: false, message: "❌ Только для администратора" };
                }
                
                const product = MiniShopDB.products.find(p => p.id === productId);
                if (product) {
                    Object.assign(product, updates);
                    return { success: true, message: `✅ Товар "${product.name}" обновлён` };
                }
                return { success: false, message: "❌ Товар не найден" };
            },
            
            // Добавление в корзину
            addToCart: function(productId, quantity = 1) {
                const product = MiniShopDB.products.find(p => p.id === productId);
                if (!product) return { success: false, message: "❌ Товар не найден" };
                if (product.stock < quantity) return { success: false, message: `❌ В наличии только ${product.stock} шт.` };
                
                const cartItem = MiniShopDB.cart.find(item => item.productId === productId);
                if (cartItem) {
                    cartItem.quantity += quantity;
                } else {
                    MiniShopDB.cart.push({
                        productId: productId,
                        name: product.name,
                        price: product.price,
                        quantity: quantity
                    });
                }
                
                this.saveCart();
                return { success: true, message: `✅ ${product.name} добавлен в корзину` };
            },
            
            // Удаление из корзины
            removeFromCart: function(productId) {
                const index = MiniShopDB.cart.findIndex(item => item.productId === productId);
                if (index !== -1) {
                    MiniShopDB.cart.splice(index, 1);
                    this.saveCart();
                    return { success: true, message: "✅ Товар удалён из корзины" };
                }
                return { success: false, message: "❌ Товар не найден в корзине" };
            },
            
            // Оформление заказа
            checkout: function() {
                if (!MiniShopDB.currentUser) return { success: false, message: "❌ Необходимо войти в систему" };
                if (MiniShopDB.cart.length === 0) return { success: false, message: "❌ Корзина пуста" };
                
                let total = 0;
                const orderItems = [];
                
                for (const item of MiniShopDB.cart) {
                    total += item.price * item.quantity;
                    orderItems.push({
                        productId: item.productId,
                        name: item.name,
                        price: item.price,
                        quantity: item.quantity
                    });
                }
                
                if (MiniShopDB.currentUser.balance < total) {
                    return { success: false, message: `❌ Недостаточно средств. Нужно: ${total}, у вас: ${MiniShopDB.currentUser.balance}` };
                }
                
                // Списываем баланс
                MiniShopDB.currentUser.balance -= total;
                
                // Уменьшаем остатки
                for (const item of MiniShopDB.cart) {
                    const product = MiniShopDB.products.find(p => p.id === item.productId);
                    if (product) product.stock -= item.quantity;
                }
                
                const order = {
                    id: MiniShopDB.nextOrderId++,
                    userId: MiniShopDB.currentUser.id,
                    username: MiniShopDB.currentUser.username,
                    items: orderItems,
                    total: total,
                    date: new Date().toLocaleString(),
                    status: "Оплачен"
                };
                
                MiniShopDB.orders.push(order);
                this.saveOrders();
                
                MiniShopDB.cart = [];
                this.saveCart();
                
                // Уведомление боту (если нужно)
                if (tg && tg.sendData) {
                    tg.sendData(JSON.stringify({
                        action: 'new_order',
                        order: order
                    }));
                }
                
                return { success: true, message: `✅ Заказ №${order.id} оформлен! Сумма: ${total}`, order: order };
            },
            
            // Пополнение баланса
            addBalance: function(amount) {
                if (!MiniShopDB.currentUser) return { success: false, message: "❌ Необходимо войти в систему" };
                MiniShopDB.currentUser.balance += amount;
                return { success: true, message: `✅ Баланс пополнен на ${amount}. Текущий баланс: ${MiniShopDB.currentUser.balance}` };
            }
        };
        
        // ============================================
        // 4. ИНТЕРФЕЙС ПОЛЬЗОВАТЕЛЯ
        // ============================================
        const UIRenderer = {
            appContainer: document.getElementById('app'),
            
            // Очистка контейнера
            clear: function() {
                this.appContainer.innerHTML = '';
            },
            
            // Кнопка администратора
            renderAdminButton: function() {
                const adminBtn = document.createElement('button');
                adminBtn.textContent = MiniShopDB.isAdminMode ? '👑 Админ режим' : '🔑 Вход для админа';
                adminBtn.style.cssText = `
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    padding: 8px 15px;
                    background: ${MiniShopDB.isAdminMode ? '#ff6b6b' : 'rgba(255,255,255,0.2)'};
                    color: white;
                    border: none;
                    border-radius: 20px;
                    font-size: 12px;
                    cursor: pointer;
                    backdrop-filter: blur(5px);
                    z-index: 1000;
                `;
                
                adminBtn.onclick = () => {
                    if (MiniShopDB.isAdminMode) {
                        ShopCore.adminLogout();
                        showNotification("Выход из админ-режима", "info");
                        this.render();
                    } else {
                        this.renderAdminLogin();
                    }
                };
                
                document.body.appendChild(adminBtn);
            },
            
            // Форма входа админа
            renderAdminLogin: function() {
                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0,0,0,0.8);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 2000;
                `;
                
                const form = document.createElement('div');
                form.style.cssText = `
                    background: white;
                    padding: 30px;
                    border-radius: 20px;
                    width: 90%;
                    max-width: 300px;
                    color: black;
                `;
                
                const title = document.createElement('h3');
                title.textContent = '👑 Вход администратора';
                title.style.marginBottom = '20px';
                
                const loginInput = document.createElement('input');
                loginInput.placeholder = 'Логин';
                loginInput.style.cssText = `
                    width: 100%;
                    padding: 10px;
                    margin: 10px 0;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                `;
                
                const passInput = document.createElement('input');
                passInput.placeholder = 'Пароль';
                passInput.type = 'password';
                passInput.style.cssText = loginInput.style.cssText;
                
                const loginBtn = document.createElement('button');
                loginBtn.textContent = 'Войти';
                loginBtn.style.cssText = `
                    width: 100%;
                    padding: 12px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    margin: 10px 0;
                    cursor: pointer;
                `;
                
                const cancelBtn = document.createElement('button');
                cancelBtn.textContent = 'Отмена';
                cancelBtn.style.cssText = `
                    width: 100%;
                    padding: 12px;
                    background: #f44336;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                `;
                
                loginBtn.onclick = () => {
                    const result = ShopCore.adminLogin(loginInput.value, passInput.value);
                    showNotification(result.message, result.success ? 'success' : 'error');
                    if (result.success) {
                        modal.remove();
                        this.render();
                    }
                };
                
                cancelBtn.onclick = () => modal.remove();
                
                form.appendChild(title);
                form.appendChild(loginInput);
                form.appendChild(passInput);
                form.appendChild(loginBtn);
                form.appendChild(cancelBtn);
                modal.appendChild(form);
                document.body.appendChild(modal);
            },
            
            // Рендеринг шапки
            renderHeader: function() {
                const header = document.createElement('div');
                header.style.cssText = `
                    background: rgba(255, 255, 255, 0.1);
                    padding: 15px;
                    border-radius: 15px;
                    margin-bottom: 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    backdrop-filter: blur(10px);
                `;
                
                const title = document.createElement('h2');
                title.textContent = '🛍️ MiniShop';
                title.style.margin = '0';
                title.style.color = 'white';
                
                header.appendChild(title);
                
                if (MiniShopDB.currentUser) {
                    const userInfo = document.createElement('div');
                    userInfo.style.cssText = `
                        display: flex;
                        align-items: center;
                        gap: 15px;
                    `;
                    
                    const balance = document.createElement('span');
                    balance.textContent = `💰 ${MiniShopDB.currentUser.balance}`;
                    balance.style.cssText = `
                        background: rgba(255, 255, 255, 0.2);
                        padding: 5px 10px;
                        border-radius: 20px;
                        font-weight: bold;
                    `;
                    
                    if (user && user.photo_url && !MiniShopDB.isAdminMode) {
                        const photo = document.createElement('img');
                        photo.src = user.photo_url;
                        photo.style.cssText = `
                            width: 30px;
                            height: 30px;
                            border-radius: 50%;
                            border: 2px solid white;
                        `;
                        userInfo.appendChild(photo);
                    }
                    
                    const username = document.createElement('span');
                    username.textContent = `👤 ${MiniShopDB.currentUser.username}`;
                    
                    userInfo.appendChild(balance);
                    userInfo.appendChild(username);
                    header.appendChild(userInfo);
                }
                
                this.appContainer.appendChild(header);
            },
            
            // Главный экран
            render: function() {
                this.clear();
                this.renderAdminButton();
                this.renderHeader();
                
                if (MiniShopDB.isAdminMode) {
                    this.renderAdminPanel();
                } else {
                    this.renderMainScreen();
                }
            },
            
            // Панель администратора
            renderAdminPanel: function() {
                const tabs = document.createElement('div');
                tabs.style.cssText = `
                    display: flex;
                    gap: 10px;
                    margin-bottom: 20px;
                `;
                
                const productsTab = document.createElement('button');
                productsTab.textContent = '📦 Товары';
                productsTab.style.cssText = this.buttonStyle(true);
                
                const addTab = document.createElement('button');
                addTab.textContent = '➕ Добавить';
                addTab.style.cssText = this.buttonStyle(false);
                
                const statsTab = document.createElement('button');
                statsTab.textContent = '📊 Статистика';
                statsTab.style.cssText = this.buttonStyle(false);
                
                tabs.appendChild(productsTab);
                tabs.appendChild(addTab);
                tabs.appendChild(statsTab);
                this.appContainer.appendChild(tabs);
                
                const content = document.createElement('div');
                this.appContainer.appendChild(content);
                
                this.renderAdminProducts(content);
                
                productsTab.onclick = () => {
                    productsTab.style.cssText = this.buttonStyle(true);
                    addTab.style.cssText = this.buttonStyle(false);
                    statsTab.style.cssText = this.buttonStyle(false);
                    this.renderAdminProducts(content);
                };
                
                addTab.onclick = () => {
                    productsTab.style.cssText = this.buttonStyle(false);
                    addTab.style.cssText = this.buttonStyle(true);
                    statsTab.style.cssText = this.buttonStyle(false);
                    this.renderAdminAddForm(content);
                };
                
                statsTab.onclick = () => {
                    productsTab.style.cssText = this.buttonStyle(false);
                    addTab.style.cssText = this.buttonStyle(false);
                    statsTab.style.cssText = this.buttonStyle(true);
                    this.renderAdminStats(content);
                };
            },
            
            // Список товаров для админа
            renderAdminProducts: function(container) {
                container.innerHTML = '';
                
                const grid = document.createElement('div');
                grid.style.cssText = `
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 15px;
                `;
                
                MiniShopDB.products.forEach(product => {
                    const card = document.createElement('div');
                    card.style.cssText = `
                        background: rgba(255, 255, 255, 0.1);
                        padding: 15px;
                        border-radius: 15px;
                        border: 1px solid rgba(255,255,255,0.2);
                        backdrop-filter: blur(10px);
                    `;
                    
                    const name = document.createElement('h3');
                    name.textContent = product.name;
                    name.style.margin = '0 0 5px 0';
                    
                    const desc = document.createElement('p');
                    desc.textContent = product.description;
                    desc.style.margin = '5px 0';
                    desc.style.fontSize = '12px';
                    desc.style.opacity = '0.8';
                    
                    const info = document.createElement('p');
                    info.textContent = `💰 ${product.price} | 📦 В наличии: ${product.stock}`;
                    info.style.margin = '5px 0';
                    info.style.fontWeight = 'bold';
                    
                    const actions = document.createElement('div');
                    actions.style.cssText = `
                        display: flex;
                        gap: 10px;
                        margin-top: 10px;
                    `;
                    
                    const editBtn = document.createElement('button');
                    editBtn.textContent = '✏️ Редактировать';
                    editBtn.style.cssText = `
                        flex: 1;
                        padding: 8px;
                        background: #2196F3;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    `;
                    
                    const deleteBtn = document.createElement('button');
                    deleteBtn.textContent = '🗑️ Удалить';
                    deleteBtn.style.cssText = `
                        flex: 1;
                        padding: 8px;
                        background: #f44336;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    `;
                    
                    editBtn.onclick = () => this.renderAdminEditForm(product);
                    deleteBtn.onclick = () => {
                        const result = ShopCore.deleteProduct(product.id);
                        showNotification(result.message, result.success ? 'success' : 'error');
                        this.render();
                    };
                    
                    actions.appendChild(editBtn);
                    actions.appendChild(deleteBtn);
                    
                    card.appendChild(name);
                    card.appendChild(desc);
                    card.appendChild(info);
                    card.appendChild(actions);
                    grid.appendChild(card);
                });
                
                container.appendChild(grid);
            },
            
            // Форма добавления товара
            renderAdminAddForm: function(container) {
                container.innerHTML = '';
                
                const form = document.createElement('div');
                form.style.cssText = `
                    background: rgba(255, 255, 255, 0.1);
                    padding: 20px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                `;
                
                const title = document.createElement('h3');
                title.textContent = '➕ Добавить новый товар';
                title.style.marginBottom = '15px';
                
                const nameInput = this.createInput('Название товара');
                const priceInput = this.createInput('Цена', 'number');
                const stockInput = this.createInput('Количество', 'number');
                const descInput = this.createInput('Описание');
                
                const addBtn = document.createElement('button');
                addBtn.textContent = '✅ Добавить товар';
                addBtn.style.cssText = `
                    width: 100%;
                    padding: 12px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    margin-top: 15px;
                    cursor: pointer;
                `;
                
                addBtn.onclick = () => {
                    const productData = {
                        name: nameInput.value,
                        price: priceInput.value,
                        stock: stockInput.value,
                        category: 'services',
                        description: descInput.value
                    };
                    
                    if (!productData.name || !productData.price || !productData.stock) {
                        showNotification('❌ Заполните все поля', 'error');
                        return;
                    }
                    
                    const result = ShopCore.addProduct(productData);
                    showNotification(result.message, result.success ? 'success' : 'error');
                    if (result.success) {
                        this.render();
                    }
                };
                
                form.appendChild(title);
                form.appendChild(nameInput);
                form.appendChild(priceInput);
                form.appendChild(stockInput);
                form.appendChild(descInput);
                form.appendChild(addBtn);
                container.appendChild(form);
            },
            
            // Форма редактирования товара
            renderAdminEditForm: function(product) {
                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0,0,0,0.8);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 2000;
                `;
                
                const form = document.createElement('div');
                form.style.cssText = `
                    background: white;
                    padding: 30px;
                    border-radius: 20px;
                    width: 90%;
                    max-width: 300px;
                    color: black;
                `;
                
                const title = document.createElement('h3');
                title.textContent = '✏️ Редактировать товар';
                title.style.marginBottom = '20px';
                
                const nameInput = document.createElement('input');
                nameInput.value = product.name;
                nameInput.placeholder = 'Название';
                nameInput.style.cssText = this.inputStyle();
                
                const priceInput = document.createElement('input');
                priceInput.value = product.price;
                priceInput.placeholder = 'Цена';
                priceInput.type = 'number';
                priceInput.style.cssText = this.inputStyle();
                
                const stockInput = document.createElement('input');
                stockInput.value = product.stock;
                stockInput.placeholder = 'Количество';
                stockInput.type = 'number';
                stockInput.style.cssText = this.inputStyle();
                
                const descInput = document.createElement('input');
                descInput.value = product.description;
                descInput.placeholder = 'Описание';
                descInput.style.cssText = this.inputStyle();
                
                const saveBtn = document.createElement('button');
                saveBtn.textContent = '💾 Сохранить';
                saveBtn.style.cssText = `
                    width: 100%;
                    padding: 12px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    margin: 10px 0;
                    cursor: pointer;
                `;
                
                const cancelBtn = document.createElement('button');
                cancelBtn.textContent = '❌ Отмена';
                cancelBtn.style.cssText = `
                    width: 100%;
                    padding: 12px;
                    background: #f44336;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                `;
                
                saveBtn.onclick = () => {
                    const updates = {
                        name: nameInput.value,
                        price: parseInt(priceInput.value),
                        stock: parseInt(stockInput.value),
                        description: descInput.value
                    };
                    
                    const result = ShopCore.editProduct(product.id, updates);
                    showNotification(result.message, result.success ? 'success' : 'error');
                    if (result.success) {
                        modal.remove();
                        this.render();
                    }
                };
                
                cancelBtn.onclick = () => modal.remove();
                
                form.appendChild(title);
                form.appendChild(nameInput);
                form.appendChild(priceInput);
                form.appendChild(stockInput);
                form.appendChild(descInput);
                form.appendChild(saveBtn);
                form.appendChild(cancelBtn);
                modal.appendChild(form);
                document.body.appendChild(modal);
            },
            
            // Статистика для админа
            renderAdminStats: function(container) {
                container.innerHTML = '';
                
                const totalUsers = MiniShopDB.users.length;
                const totalOrders = MiniShopDB.orders.length;
                const totalRevenue = MiniShopDB.orders.reduce((sum, o) => sum + o.total, 0);
                const totalProducts = MiniShopDB.products.reduce((sum, p) => sum + p.stock, 0);
                
                const stats = [
                    { label: '👥 Пользователей', value: totalUsers },
                    { label: '📦 Заказов', value: totalOrders },
                    { label: '💰 Выручка', value: totalRevenue },
                    { label: '📦 Товаров в наличии', value: totalProducts }
                ];
                
                const grid = document.createElement('div');
                grid.style.cssText = `
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                `;
                
                stats.forEach(stat => {
                    const card = document.createElement('div');
                    card.style.cssText = `
                        background: rgba(255, 255, 255, 0.1);
                        padding: 20px;
                        border-radius: 15px;
                        text-align: center;
                        backdrop-filter: blur(10px);
                    `;
                    
                    const value = document.createElement('div');
                    value.textContent = stat.value;
                    value.style.cssText = `
                        font-size: 24px;
                        font-weight: bold;
                        margin-bottom: 5px;
                    `;
                    
                    const label = document.createElement('div');
                    label.textContent = stat.label;
                    label.style.opacity = '0.8';
                    
                    card.appendChild(value);
                    card.appendChild(label);
                    grid.appendChild(card);
                });
                
                container.appendChild(grid);
            },
            
            // Основной экран для пользователей
            renderMainScreen: function() {
                const tabs = document.createElement('div');
                tabs.style.cssText = `
                    display: flex;
                    gap: 10px;
                    margin-bottom: 20px;
                `;
                
                const catalogTab = document.createElement('button');
                catalogTab.textContent = '📦 Каталог';
                catalogTab.style.cssText = this.buttonStyle(true);
                
                const cartTab = document.createElement('button');
                cartTab.textContent = `🛒 Корзина (${MiniShopDB.cart.reduce((sum, item) => sum + item.quantity, 0)})`;
                cartTab.style.cssText = this.buttonStyle(false);
                
                const ordersTab = document.createElement('button');
                ordersTab.textContent = '📋 Заказы';
                ordersTab.style.cssText = this.buttonStyle(false);
                
                tabs.appendChild(catalogTab);
                tabs.appendChild(cartTab);
                tabs.appendChild(ordersTab);
                this.appContainer.appendChild(tabs);
                
                const content = document.createElement('div');
                this.appContainer.appendChild(content);
                
                this.renderCatalog(content);
                
                catalogTab.onclick = () => {
                    catalogTab.style.cssText = this.buttonStyle(true);
                    cartTab.style.cssText = this.buttonStyle(false);
                    ordersTab.style.cssText = this.buttonStyle(false);
                    this.renderCatalog(content);
                };
                
                cartTab.onclick = () => {
                    catalogTab.style.cssText = this.buttonStyle(false);
                    cartTab.style.cssText = this.buttonStyle(true);
                    ordersTab.style.cssText = this.buttonStyle(false);
                    this.renderCart(content);
                };
                
                ordersTab.onclick = () => {
                    catalogTab.style.cssText = this.buttonStyle(false);
                    cartTab.style.cssText = this.buttonStyle(false);
                    ordersTab.style.cssText = this.buttonStyle(true);
                    this.renderOrders(content);
                };
            },
            
            // Каталог
            renderCatalog: function(container) {
                container.innerHTML = '';
                
                const grid = document.createElement('div');
                grid.style.cssText = `
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 15px;
                `;
                
                MiniShopDB.products.forEach(product => {
                    const card = document.createElement('div');
                    card.style.cssText = `
                        background: rgba(255, 255, 255, 0.1);
                        padding: 15px;
                        border-radius: 15px;
                        border: 1px solid rgba(255,255,255,0.2);
                        backdrop-filter: blur(10px);
                    `;
                    
                    const name = document.createElement('h3');
                    name.textContent = product.name;
                    name.style.margin = '0 0 5px 0';
                    
                    const desc = document.createElement('p');
                    desc.textContent = product.description;
                    desc.style.margin = '5px 0';
                    desc.style.fontSize = '12px';
                    desc.style.opacity = '0.8';
                    
                    const price = document.createElement('p');
                    price.textContent = `💰 ${product.price} | 📦 В наличии: ${product.stock}`;
                    price.style.margin = '5px 0';
                    price.style.fontWeight = 'bold';
                    
                    const buyBtn = document.createElement('button');
                    buyBtn.textContent = '➕ В корзину';
                    buyBtn.style.cssText = `
                        width: 100%;
                        padding: 10px;
                        background: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        margin-top: 10px;
                        cursor: pointer;
                    `;
                    
                    buyBtn.onclick = () => {
                        const result = ShopCore.addToCart(product.id, 1);
                        showNotification(result.message, result.success ? 'success' : 'error');
                        this.render();
                    };
                    
                    card.appendChild(name);
                    card.appendChild(desc);
                    card.appendChild(price);
                    card.appendChild(buyBtn);
                    grid.appendChild(card);
                });
                
                container.appendChild(grid);
            },
            
            // Корзина
            renderCart: function(container) {
                container.innerHTML = '';
                
                if (MiniShopDB.cart.length === 0) {
                    const empty = document.createElement('div');
                    empty.textContent = '🛒 Корзина пуста';
                    empty.style.cssText = `
                        text-align: center;
                        padding: 50px;
                        background: rgba(255,255,255,0.1);
                        border-radius: 15px;
                        backdrop-filter: blur(10px);
                    `;
                    container.appendChild(empty);
                    return;
                }
                
                const cartList = document.createElement('div');
                cartList.style.cssText = `
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    margin-bottom: 20px;
                `;
                
                let total = 0;
                
                MiniShopDB.cart.forEach(item => {
                    const itemTotal = item.price * item.quantity;
                    total += itemTotal;
                    
                    const cartItem = document.createElement('div');
                    cartItem.style.cssText = `
                        background: rgba(255, 255, 255, 0.1);
                        padding: 10px;
                        border-radius: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        backdrop-filter: blur(10px);
                    `;
                    
                    const info = document.createElement('div');
                    info.innerHTML = `<strong>${item.name}</strong><br>${item.price} × ${item.quantity} = ${itemTotal}`;
                    
                    const removeBtn = document.createElement('button');
                    removeBtn.textContent = '❌';
                    removeBtn.style.cssText = `
                        background: none;
                        border: none;
                        color: #ff6b6b;
                        font-size: 20px;
                        cursor: pointer;
                        padding: 5px;
                    `;
                    
                    removeBtn.onclick = () => {
                        ShopCore.removeFromCart(item.productId);
                        showNotification('Товар удалён', 'info');
                        this.render();
                    };
                    
                    cartItem.appendChild(info);
                    cartItem.appendChild(removeBtn);
                    cartList.appendChild(cartItem);
                });
                
                container.appendChild(cartList);
                
                const totalDiv = document.createElement('div');
                totalDiv.style.cssText = `
                    background: rgba(255, 255, 255, 0.2);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 15px 0;
                    text-align: center;
                    font-size: 18px;
                    font-weight: bold;
                    backdrop-filter: blur(10px);
                `;
                totalDiv.textContent = `ИТОГО: ${total}`;
                container.appendChild(totalDiv);
                
                const checkoutBtn = document.createElement('button');
                checkoutBtn.textContent = '✅ Оформить заказ';
                checkoutBtn.style.cssText = `
                    width: 100%;
                    padding: 15px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                `;
                
                checkoutBtn.onclick = () => {
                    const result = ShopCore.checkout();
                    showNotification(result.message, result.success ? 'success' : 'error');
                    if (result.success) {
                        this.render();
                    }
                };
                
                container.appendChild(checkoutBtn);
            },
            
            // История заказов
            renderOrders: function(container) {
                container.innerHTML = '';
                
                const userOrders = MiniShopDB.orders.filter(o => o.userId === MiniShopDB.currentUser?.id);
                
                if (userOrders.length === 0) {
                    const empty = document.createElement('div');
                    empty.textContent = '📭 У вас пока нет заказов';
                    empty.style.cssText = `
                        text-align: center;
                        padding: 50px;
                        background: rgba(255,255,255,0.1);
                        border-radius: 15px;
                        backdrop-filter: blur(10px);
                    `;
                    container.appendChild(empty);
                    return;
                }
                
                const ordersList = document.createElement('div');
                ordersList.style.cssText = `
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                `;
                
                userOrders.forEach(order => {
                    const orderCard = document.createElement('div');
                    orderCard.style.cssText = `
                        background: rgba(255, 255, 255, 0.1);
                        padding: 15px;
                        border-radius: 15px;
                        backdrop-filter: blur(10px);
                    `;
                    
                    const header = document.createElement('div');
                    header.style.cssText = `
                        display: flex;
                        justify-content: space-between;
                        margin-bottom: 10px;
                    `;
                    header.innerHTML = `<strong>Заказ №${order.id}</strong> <span>${order.date}</span>`;
                    
                    const items = document.createElement('div');
                    items.style.fontSize = '12px';
                    items.innerHTML = order.items.map(item => 
                        `${item.name} × ${item.quantity} = ${item.price * item.quantity}`
                    ).join('<br>');
                    
                    const total = document.createElement('div');
                    total.style.cssText = `
                        margin-top: 10px;
                        text-align: right;
                        font-weight: bold;
                    `;
                    total.textContent = `Сумма: ${order.total} | Статус: ${order.status}`;
                    
                    orderCard.appendChild(header);
                    orderCard.appendChild(items);
                    orderCard.appendChild(total);
                    ordersList.appendChild(orderCard);
                });
                
                container.appendChild(ordersList);
            },
            
            // Вспомогательные стили
            buttonStyle: function(active) {
                return active ?
                    `flex: 1; padding: 12px; background: #4CAF50; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; backdrop-filter: blur(5px);` :
                    `flex: 1; padding: 12px; background: rgba(255,255,255,0.2); color: white; border: none; border-radius: 10px; cursor: pointer; backdrop-filter: blur(5px);`;
            },
            
            inputStyle: function() {
                return `
                    width: 100%;
                    padding: 10px;
                    margin: 8px 0;
                    border: 1px solid rgba(255,255,255,0.2);
                    border-radius: 8px;
                    background: rgba(255,255,255,0.9);
                    font-size: 14px;
                    box-sizing: border-box;
                `;
            },
            
            createInput: function(placeholder, type = 'text') {
                const input = document.createElement('input');
                input.placeholder = placeholder;
                input.type = type;
                input.style.cssText = this.inputStyle();
                return input;
            }
        };
        
        // ============================================
        // 5. ЗАПУСК ПРИЛОЖЕНИЯ
        // ============================================
        setTimeout(() => {
            UIRenderer.render();
            console.log("✅ Мини-магазин загружен!");
        }, 500);
    </script>
</body>
</html>
