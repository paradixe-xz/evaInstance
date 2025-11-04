#!/usr/bin/env python3
"""
Script de prueba para todas las APIs de Tous Software Corp
- API de Leads
- API de Órdenes  
- API de Pagos

Autor: Eva AI System
Fecha: 2025-10-28
"""

import requests
import json
from datetime import datetime, timedelta
import sys

class TouscorpAPITester:
    def __init__(self):
        self.base_url = "https://tsc-api-925835182876.us-east1.run.app/api/v1/1998010101"
        self.token = "CVWM45F2ASA3O6SLDDFHP19JPULZ8FZL42PVKZU65ZHMRUPVSEFBK11Y5GPOXOA0"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        self.created_leads = []
        self.created_orders = []
        self.processed_payments = []

    def print_header(self, title):
        """Imprime un header bonito"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)

    def print_response(self, response, request_data=None):
        """Imprime la respuesta de manera formateada"""
        print(f"\n📤 REQUEST:")
        if request_data:
            print(json.dumps(request_data, indent=2, ensure_ascii=False))
        
        print(f"\n📥 RESPONSE (Status: {response.status_code}):")
        try:
            response_data = response.json()
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            return response_data
        except:
            print(response.text)
            return None

    def test_create_lead(self):
        """Prueba crear un lead"""
        self.print_header("🧑‍💼 PRUEBA: CREAR LEAD")
        
        lead_data = {
            "name": "Juan Carlos",
            "last_name": "Pérez García",
            "email": "juan.perez@testmail.com",
            "phone_number": "9548093102",
            "media": "WEB",
            "entervia": "9548092011",
            "product": "API_TEST_PRODUCT",
            "address": "Calle Principal 123",
            "city": "Miami",
            "state": "FL",
            "zip": "33101",
            "zip4": "1234",
            "country": "US",
            "comment": "Lead de prueba creado por script Python",
            "addInfo": {
                "tscReference": "DEFAULT",
                "data": [
                    {"tscReferenceCode": "TSCREF1", "tscReferenceValue": "PYTHON_TEST"},
                    {"tscReferenceCode": "TSCREF2", "tscReferenceValue": "API_SCRIPT"}
                ]
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/leads",
                headers=self.headers,
                json=lead_data,
                timeout=30
            )
            
            result = self.print_response(response, lead_data)
            
            if result and result.get('rescode') == '000':
                lead_num = result.get('leadnum')
                self.created_leads.append(lead_num)
                print(f"\n✅ Lead creado exitosamente: #{lead_num}")
                return lead_num
            else:
                print(f"\n❌ Error creando lead: {result}")
                return None
                
        except Exception as e:
            print(f"\n💥 Error de conexión: {e}")
            return None

    def test_update_lead(self, lead_num):
        """Prueba actualizar un lead"""
        if not lead_num:
            print("\n⚠️  No hay lead para actualizar")
            return False
            
        self.print_header(f"📝 PRUEBA: ACTUALIZAR LEAD #{lead_num}")
        
        update_data = {
            "entervia": "9548092011",
            "comment": "Lead actualizado por script Python - Nueva información",
            "name": "Juan Carlos",
            "last_name": "Pérez García ACTUALIZADO",
            "phone_number": "9548093199",  # Nuevo teléfono
            "addInfo": {
                "tscReference": "DEFAULT",
                "data": [
                    {"tscReferenceCode": "TSCREF1", "tscReferenceValue": "UPDATED_PYTHON"},
                    {"tscReferenceCode": "TSCREF2", "tscReferenceValue": "SCRIPT_UPDATE"}
                ]
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/leads/{lead_num}",
                headers=self.headers,
                json=update_data,
                timeout=30
            )
            
            result = self.print_response(response, update_data)
            
            if result and result.get('rescode') == '000':
                print(f"\n✅ Lead #{lead_num} actualizado exitosamente")
                return True
            else:
                print(f"\n❌ Error actualizando lead: {result}")
                return False
                
        except Exception as e:
            print(f"\n💥 Error de conexión: {e}")
            return False

    def test_create_order(self, lead_num=None):
        """Prueba crear una orden"""
        self.print_header("🛒 PRUEBA: CREAR ORDEN")
        
        today = datetime.now().strftime("%Y-%m-%d")
        delivery_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        order_data = {
            "createBy": "PYTHON_SCRIPT",
            "seller": "PYTHON_SCRIPT",
            "sellerName": "Script Python Tester",
            "company": "90001",
            "department": "90001",
            "ordenDate": today,
            "leadnum": lead_num or "12345",  # Usar lead creado o número de prueba
            "customerName": "María Elena",
            "customerLastname": "Rodríguez López",
            "direction": {
                "address": "2200 NW 72ND AVE STOP 3",
                "city": "MIAMI",
                "state": "FL",
                "zip": "33152",
                "zip4": "9418",
                "country": "US",
                "urbanization": "Brickell"
            },
            "phone1": "9548093100",
            "phone2": "9548093101",
            "comment": "Orden de prueba creada por script Python",
            "payterm": "PREPAID",
            "deliveryDate": delivery_date,
            "shipvia": "USPS",
            "subTotal": 250.00,
            "total": 250.00,
            "saleTax": 0,
            "taxes": 0,
            "paid": 0,
            "discount": 0,
            "discountAmount": 0,
            "detail": [
                {
                    "productCode": "PYTHON_TEST_01",
                    "packageCode": "",
                    "qty": 2,
                    "total": 200.00,
                    "pricePerUnit": 100.00
                },
                {
                    "productCode": "PYTHON_TEST_02", 
                    "packageCode": "",
                    "qty": 1,
                    "total": 50.00,
                    "pricePerUnit": 50.00
                }
            ]
        }

        try:
            response = requests.post(
                f"{self.base_url}/order",
                headers=self.headers,
                json=order_data,
                timeout=30
            )
            
            result = self.print_response(response, order_data)
            
            if result and result.get('rescode') == '000':
                order_num = result.get('ordernum')
                self.created_orders.append(order_num)
                print(f"\n✅ Orden creada exitosamente: #{order_num}")
                return order_num
            else:
                print(f"\n❌ Error creando orden: {result}")
                return None
                
        except Exception as e:
            print(f"\n💥 Error de conexión: {e}")
            return None

    def test_process_payment(self, order_num=None, lead_num=None):
        """Prueba procesar un pago"""
        self.print_header("💳 PRUEBA: PROCESAR PAGO")
        
        payment_data = {
            "processpayment": "Y",
            "seller": "PYTHON_SCRIPT",
            "sellerName": "Script Python Tester",
            "company": "1998010101",
            "department": "100",
            "ordernum": order_num or "2251",  # Usar orden creada o número de prueba
            "leadnum": lead_num or "1239",   # Usar lead creado o número de prueba
            "customerName": "Carlos Alberto",
            "customerLastname": "Mendoza Silva",
            "direction": {
                "address": "Av. Principal #123",
                "city": "Miramar",
                "state": "FL",
                "zip": "10101",
                "zip4": "0001",
                "country": "US",
                "urbanization": "Ensanche Piantini"
            },
            "phone1": "9088908899",
            "phone2": "9088908898",
            "comment": "Pago de prueba procesado por script Python",
            "payterm": "CC",
            "paytype": "CC",
            "merchat": "TSCTEST",
            "payment_amt": 150.75,
            "cardnumber": "4111111111111111",  # Número de prueba Visa
            "email": "carlos.mendoza@testmail.com",
            "expdate": "12/27",
            "cvv": "123"
        }

        try:
            response = requests.post(
                f"{self.base_url}/payment",
                headers=self.headers,
                json=payment_data,
                timeout=30
            )
            
            result = self.print_response(response, payment_data)
            
            if result and result.get('rescode') == '000':
                receipt_id = result.get('receiptid')
                auth_code = result.get('authcode')
                transaction_id = result.get('transactionid')
                self.processed_payments.append(receipt_id)
                
                print(f"\n✅ Pago procesado exitosamente!")
                print(f"   Receipt ID: #{receipt_id}")
                print(f"   Auth Code: {auth_code}")
                print(f"   Transaction ID: {transaction_id}")
                print(f"   Status: {result.get('longmsg', 'APPROVED')}")
                return receipt_id
            else:
                print(f"\n❌ Error procesando pago: {result}")
                return None
                
        except Exception as e:
            print(f"\n💥 Error de conexión: {e}")
            return None

    def test_all_apis_flow(self):
        """Prueba el flujo completo: Lead -> Orden -> Pago"""
        self.print_header("🔄 FLUJO COMPLETO: LEAD → ORDEN → PAGO")
        
        print("Iniciando flujo completo de pruebas...")
        
        # 1. Crear Lead
        print("\n1️⃣ Creando lead...")
        lead_num = self.test_create_lead()
        
        if not lead_num:
            print("❌ No se pudo crear el lead. Deteniendo flujo.")
            return False
        
        # 2. Actualizar Lead
        print("\n2️⃣ Actualizando lead...")
        self.test_update_lead(lead_num)
        
        # 3. Crear Orden
        print("\n3️⃣ Creando orden...")
        order_num = self.test_create_order(lead_num)
        
        if not order_num:
            print("❌ No se pudo crear la orden. Continuando con pago de prueba.")
        
        # 4. Procesar Pago
        print("\n4️⃣ Procesando pago...")
        receipt_id = self.test_process_payment(order_num, lead_num)
        
        # Resumen final
        self.print_header("📊 RESUMEN DEL FLUJO COMPLETO")
        print(f"✅ Lead creado: #{lead_num}")
        print(f"✅ Orden creada: #{order_num or 'N/A'}")
        print(f"✅ Pago procesado: #{receipt_id or 'N/A'}")
        
        return True

    def show_summary(self):
        """Muestra un resumen de todas las pruebas"""
        self.print_header("📋 RESUMEN DE TODAS LAS PRUEBAS")
        
        print(f"🧑‍💼 Leads creados: {len(self.created_leads)}")
        for lead in self.created_leads:
            print(f"   - Lead #{lead}")
        
        print(f"\n🛒 Órdenes creadas: {len(self.created_orders)}")
        for order in self.created_orders:
            print(f"   - Orden #{order}")
        
        print(f"\n💳 Pagos procesados: {len(self.processed_payments)}")
        for payment in self.processed_payments:
            print(f"   - Receipt #{payment}")

    def run_menu(self):
        """Ejecuta el menú principal"""
        while True:
            print("\n" + "="*60)
            print("  🧪 TESTER DE APIs TOUS SOFTWARE CORP")
            print("="*60)
            print("1. 🧑‍💼 Probar API de Leads (Crear)")
            print("2. 📝 Probar API de Leads (Actualizar)")
            print("3. 🛒 Probar API de Órdenes")
            print("4. 💳 Probar API de Pagos")
            print("5. 🔄 Flujo Completo (Lead → Orden → Pago)")
            print("6. 📊 Ver Resumen")
            print("7. 🚪 Salir")
            print("-"*60)
            
            try:
                choice = input("Selecciona una opción (1-7): ").strip()
                
                if choice == '1':
                    self.test_create_lead()
                
                elif choice == '2':
                    if self.created_leads:
                        lead_num = self.created_leads[-1]  # Usar el último lead creado
                        self.test_update_lead(lead_num)
                    else:
                        lead_num = input("Ingresa el número de lead a actualizar: ").strip()
                        if lead_num:
                            self.test_update_lead(lead_num)
                        else:
                            print("❌ Número de lead requerido")
                
                elif choice == '3':
                    lead_num = self.created_leads[-1] if self.created_leads else None
                    self.test_create_order(lead_num)
                
                elif choice == '4':
                    order_num = self.created_orders[-1] if self.created_orders else None
                    lead_num = self.created_leads[-1] if self.created_leads else None
                    self.test_process_payment(order_num, lead_num)
                
                elif choice == '5':
                    self.test_all_apis_flow()
                
                elif choice == '6':
                    self.show_summary()
                
                elif choice == '7':
                    print("\n👋 ¡Gracias por usar el tester de APIs!")
                    self.show_summary()
                    break
                
                else:
                    print("❌ Opción inválida. Por favor selecciona 1-7.")
                
                input("\n⏸️  Presiona Enter para continuar...")
                
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"\n💥 Error inesperado: {e}")
                input("⏸️  Presiona Enter para continuar...")

def main():
    """Función principal"""
    print("🚀 Iniciando Tester de APIs de Tous Software Corp...")
    
    tester = TouscorpAPITester()
    
    try:
        tester.run_menu()
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
