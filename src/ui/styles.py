# styles.py
def get_css_styles():
    """Возвращает CSS стили для приложения"""
    return """
    <style>
        /* Основные стили */
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1E3A8A;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #E5E7EB;
        }

        .section-header {
            font-size: 1.5rem;
            font-weight: 600;
            color: #374151;
            margin: 1.5rem 0 1rem 0;
        }

        .card {
            background-color: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border: 1px solid #E5E7EB;
            margin-bottom: 1.5rem;
        }

        .metric-card {
            background: white;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1E3A8A;
            margin: 0.5rem 0;
        }

        .metric-label {
            font-size: 0.875rem;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            font-size: 0.875rem;
        }

        .data-table thead {
            background-color: #F9FAFB;
        }

        .data-table th {
            padding: 0.75rem 1rem;
            text-align: left;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #E5E7EB;
            white-space: nowrap;
        }

        .data-table td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #E5E7EB;
            color: #4B5563;
        }

        .data-table tbody tr:hover {
            background-color: #F9FAFB;
        }

        .status-processing {
            color: #F59E0B;
            font-weight: 600;
        }

        .status-completed {
            color: #10B981;
            font-weight: 600;
        }

        .status-error {
            color: #EF4444;
            font-weight: 600;
        }

        .action-button {
            background: none;
            border: none;
            cursor: pointer;
            padding: 0.25rem;
            margin: 0 0.125rem;
            border-radius: 4px;
            transition: background-color 0.2s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        .action-button:hover {
            background-color: #F3F4F6;
        }

        .search-container {
            position: relative;
            width: 100%;
        }

        .search-input {
            width: 100%;
            padding: 0.5rem 2.5rem 0.5rem 0.75rem;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            font-size: 0.875rem;
            transition: border-color 0.2s;
        }

        .search-input:focus {
            outline: none;
            border-color: #4F46E5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }

        .search-icon {
            position: absolute;
            right: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            color: #6B7280;
        }

        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.75rem;
            margin-top: 1.5rem;
        }

        .pagination-button {
            padding: 0.5rem 1rem;
            background-color: white;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            color: #374151;
            transition: all 0.2s;
            min-width: 80px;
        }

        .pagination-button:hover:not(:disabled) {
            background-color: #F9FAFB;
            border-color: #9CA3AF;
        }

        .pagination-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .current-page {
            font-weight: 600;
            color: #374151;
            font-size: 0.875rem;
        }

        .step-indicator {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            padding: 0.75rem;
            background-color: #F9FAFB;
            border-radius: 6px;
            border-left: 4px solid #4F46E5;
        }

        .step-number {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            background-color: #4F46E5;
            color: white;
            border-radius: 50%;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.75rem;
        }

        .step-text {
            flex: 1;
        }

        .step-title {
            font-weight: 600;
            color: #374151;
            font-size: 0.875rem;
        }

        .step-description {
            color: #6B7280;
            font-size: 0.75rem;
            margin-top: 0.125rem;
        }

        .tab-content {
            animation: fadeIn 0.3s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .control-panel {
            background-color: #F9FAFB;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .control-label {
            font-size: 0.875rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 0.5rem;
            display: block;
        }

        .control-select {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            font-size: 0.875rem;
            background-color: white;
        }

        .add-button {
            padding: 0.5rem 1rem;
            background-color: white;
            border: 1px solid #4F46E5;
            color: #4F46E5;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .add-button:hover {
            background-color: #4F46E5;
            color: white;
        }

        .sidebar-section {
            background-color: white;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 1px solid #E5E7EB;
        }

        .sidebar-title {
            font-size: 1rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 1rem;
        }

        .status-item {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }

        .status-online {
            background-color: #10B981;
        }

        .status-warning {
            background-color: #F59E0B;
        }

        .status-offline {
            background-color: #EF4444;
        }

        .quick-action {
            padding: 0.75rem;
            background-color: white;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            cursor: pointer;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
            color: #374151;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            width: 100%;
            text-align: left;
        }

        .quick-action:hover {
            background-color: #F9FAFB;
            border-color: #D1D5DB;
        }
        
        /* Новые стили для поиска по колонке */
        .search-column-select {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            font-size: 0.875rem;
            background-color: white;
        }
        
        .search-column-select:focus {
            outline: none;
            border-color: #4F46E5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        
        .search-info-box {
            background-color: #F0F9FF;
            border: 1px solid #BAE6FD;
            border-radius: 6px;
            padding: 0.75rem;
            margin-bottom: 1rem;
            font-size: 0.875rem;
        }
        
        .reset-button {
            padding: 0.5rem 1rem;
            background-color: white;
            border: 1px solid #D1D5DB;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.875rem;
            color: #374151;
            transition: all 0.2s;
            width: 100%;
        }
        
        .reset-button:hover {
            background-color: #F9FAFB;
            border-color: #9CA3AF;
        }
        
    </style>
    """