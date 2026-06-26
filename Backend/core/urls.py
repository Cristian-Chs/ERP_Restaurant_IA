# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MenuListView, listar_ingredientes, filtrar_productos,
    productos_view, check_user_and_get_reset_link,
    ProductViewSet, IngredientViewSet, FlavorViewSet, AdminStatsView, SalesPredictionView, TelegramLoginView,
    ExportFinancialPDFView, ExportPayrollPDFView, EmployeeViewSet, PayrollPaymentViewSet,
    PriceOptimizationAPI, DemandPredictionAPI, CurrencyRatesAPI, UpdateCurrencyRateAPI, RecipeViewSet,
    TableViewSet, TableAvailabilityView # 
)
from .analytics_views import (
    DynamicCostRecalculationView, BCGMatrixView, PurchasePredictionView, ExportExcelFinancialView
)

router = DefaultRouter()
router.register(r'products-admin', ProductViewSet, basename='product-admin')
router.register(r'ingredients-admin', IngredientViewSet, basename='ingredient-admin')
router.register(r'flavors-admin', FlavorViewSet, basename='flavor-admin')
router.register(r'recipes-admin', RecipeViewSet, basename='recipe-admin') #  URL Recetario
router.register(r'tables', TableViewSet, basename='table') # MESA MANAGEMENT
#  URLs RRHH
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'payroll', PayrollPaymentViewSet, basename='payroll')

urlpatterns = [
    path("tables/availability/", TableAvailabilityView.as_view(), name="table-availability"),
    path('', include(router.urls)),
    path("products/", MenuListView.as_view(), name="menu-list-grouped"),
    path("ingredientes/", listar_ingredientes, name="listar_ingredientes"),
    path("productos/", filtrar_productos, name="filtrar_productos"),
    path("productos/", productos_view),
    
    # Dashboard stats
    path("admin/stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("admin/prediction/", SalesPredictionView.as_view(), name="admin-prediction"),
    path("auth/telegram/", TelegramLoginView.as_view(), name="telegram-auth"),
    
    # Export
    path("admin/export/pdf/", ExportFinancialPDFView.as_view(), name="export-pdf"),
    path("admin/export/payroll-pdf/", ExportPayrollPDFView.as_view(), name="export-payroll-pdf"),
    
    #  Analytics con Pandas
    path("analytics/recalculate-costs/", DynamicCostRecalculationView.as_view(), name="recalculate-costs"),
    path("analytics/bcg-matrix/", BCGMatrixView.as_view(), name="bcg-matrix"),
    path("analytics/purchase-suggestions/", PurchasePredictionView.as_view(), name="purchase-suggestions"),
    path("analytics/export-excel/", ExportExcelFinancialView.as_view(), name="export-excel"),
    path("analytics/price-suggestion/<int:product_id>/", PriceOptimizationAPI.as_view(), name="price-suggestion"), # 
    path("analytics/demand-prediction/", DemandPredictionAPI.as_view(), name="demand-prediction"),
    path("currency/rates/", CurrencyRatesAPI.as_view(), name="currency-rates"), # 
    path("currency/update-rate/", UpdateCurrencyRateAPI.as_view(), name="update-currency-rate"), # 
]