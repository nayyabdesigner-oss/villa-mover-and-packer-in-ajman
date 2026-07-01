"""Customer management for the moving service."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Customer:
    name: str
    email: str
    phone: str
    address: str
    customer_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    total_bookings: int = 0
    is_active: bool = True
    notes: str = ""


class CustomerManager:
    """Manages customer records and validation."""

    def __init__(self):
        self._customers: dict[str, Customer] = {}
        self._next_id: int = 1

    @property
    def customer_count(self) -> int:
        return len(self._customers)

    def register_customer(
        self,
        name: str,
        email: str,
        phone: str,
        address: str,
        notes: str = "",
    ) -> Customer:
        """Register a new customer after validation."""
        self._validate_name(name)
        self._validate_email(email)
        self._validate_phone(phone)
        self._validate_address(address)
        self._check_duplicate_email(email)

        customer_id = f"CUST-{self._next_id:05d}"
        self._next_id += 1

        customer = Customer(
            name=name.strip(),
            email=email.strip().lower(),
            phone=self._normalize_phone(phone),
            address=address.strip(),
            customer_id=customer_id,
            notes=notes,
        )
        self._customers[customer_id] = customer
        return customer

    def get_customer(self, customer_id: str) -> Customer:
        """Retrieve a customer by ID."""
        if customer_id not in self._customers:
            raise KeyError(f"Customer not found: {customer_id}")
        return self._customers[customer_id]

    def find_by_email(self, email: str) -> Optional[Customer]:
        """Find a customer by email address."""
        normalized = email.strip().lower()
        for customer in self._customers.values():
            if customer.email == normalized:
                return customer
        return None

    def find_by_phone(self, phone: str) -> Optional[Customer]:
        """Find a customer by phone number."""
        normalized = self._normalize_phone(phone)
        for customer in self._customers.values():
            if customer.phone == normalized:
                return customer
        return None

    def update_customer(self, customer_id: str, **kwargs) -> Customer:
        """Update customer fields."""
        customer = self.get_customer(customer_id)

        if "name" in kwargs:
            self._validate_name(kwargs["name"])
            customer.name = kwargs["name"].strip()
        if "email" in kwargs:
            self._validate_email(kwargs["email"])
            new_email = kwargs["email"].strip().lower()
            if new_email != customer.email:
                self._check_duplicate_email(new_email)
                customer.email = new_email
        if "phone" in kwargs:
            self._validate_phone(kwargs["phone"])
            customer.phone = self._normalize_phone(kwargs["phone"])
        if "address" in kwargs:
            self._validate_address(kwargs["address"])
            customer.address = kwargs["address"].strip()
        if "notes" in kwargs:
            customer.notes = kwargs["notes"]

        return customer

    def deactivate_customer(self, customer_id: str) -> Customer:
        """Deactivate a customer account."""
        customer = self.get_customer(customer_id)
        if not customer.is_active:
            raise ValueError(f"Customer {customer_id} is already inactive")
        customer.is_active = False
        return customer

    def reactivate_customer(self, customer_id: str) -> Customer:
        """Reactivate a customer account."""
        customer = self.get_customer(customer_id)
        if customer.is_active:
            raise ValueError(f"Customer {customer_id} is already active")
        customer.is_active = True
        return customer

    def get_active_customers(self) -> list[Customer]:
        """Get all active customers."""
        return [c for c in self._customers.values() if c.is_active]

    def search_customers(self, query: str) -> list[Customer]:
        """Search customers by name, email, or phone."""
        if not query or not query.strip():
            return []
        q = query.strip().lower()
        return [
            c for c in self._customers.values()
            if q in c.name.lower() or q in c.email or q in c.phone
        ]

    def increment_booking_count(self, customer_id: str) -> None:
        """Increment the total bookings count for a customer."""
        customer = self.get_customer(customer_id)
        customer.total_bookings += 1

    def is_returning_customer(self, customer_id: str) -> bool:
        """Check if a customer has previous bookings."""
        customer = self.get_customer(customer_id)
        return customer.total_bookings > 0

    def _validate_name(self, name: str) -> None:
        if not name or not name.strip():
            raise ValueError("Customer name is required")
        if len(name.strip()) < 2:
            raise ValueError("Customer name must be at least 2 characters")

    def _validate_email(self, email: str) -> None:
        if not email or not email.strip():
            raise ValueError("Email is required")
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email.strip()):
            raise ValueError(f"Invalid email format: {email}")

    def _validate_phone(self, phone: str) -> None:
        if not phone or not phone.strip():
            raise ValueError("Phone number is required")
        digits = re.sub(r"[^\d+]", "", phone)
        if len(digits) < 7 or len(digits) > 15:
            raise ValueError(f"Invalid phone number: {phone}")

    def _validate_address(self, address: str) -> None:
        if not address or not address.strip():
            raise ValueError("Address is required")
        if len(address.strip()) < 10:
            raise ValueError("Address must be at least 10 characters")

    def _normalize_phone(self, phone: str) -> str:
        return re.sub(r"[^\d+]", "", phone)

    def _check_duplicate_email(self, email: str) -> None:
        normalized = email.strip().lower()
        for customer in self._customers.values():
            if customer.email == normalized:
                raise ValueError(f"Email already registered: {email}")
