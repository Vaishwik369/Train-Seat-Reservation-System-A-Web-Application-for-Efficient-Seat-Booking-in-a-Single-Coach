# app.py
import streamlit as st
import sqlite3
from sqlite3 import Error

class TrainSeatReservation:
    def __init__(self):
        self.connection = self.create_connection("train_reservation.db")
        self.create_tables()
        self.seats = self.load_seats()

    def create_connection(self, db_file):
        """Create a database connection to the SQLite database."""
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print(e)
        return conn

    def create_tables(self):
        """Create tables if they don't exist."""
        create_seats_table = """
        CREATE TABLE IF NOT EXISTS seats (
            seat_id INTEGER PRIMARY KEY,
            status BOOLEAN
        );
        """
        create_reservations_table = """
        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seat_ids TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor = self.connection.cursor()
        cursor.execute(create_seats_table)
        cursor.execute(create_reservations_table)
        self.connection.commit()

        # Initialize seat statuses if not already done
        self.init_seats()

    def init_seats(self):
        """Initialize seat statuses in the database."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM seats")
        count = cursor.fetchone()[0]

        if count == 0:  # If the seats table is empty, initialize it
            for seat_id in range(80):
                status = 0 if seat_id not in [0, 1, 2, 15, 22, 23, 33, 34, 35] else 1
                cursor.execute("INSERT INTO seats (seat_id, status) VALUES (?, ?)", (seat_id, status))
            self.connection.commit()

    def load_seats(self):
        """Load seat statuses from the database."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT seat_id, status FROM seats")
        return [row[1] for row in cursor.fetchall()]

    def display_seats(self):
        """Display the seat availability."""
        seat_display = []
        for status in self.seats:
            seat_symbol = "X" if status == 1 else "O"
            seat_display.append(seat_symbol)
        return seat_display

    def book_seats(self, required_seats):
        """Book the required number of seats."""
        available_seats = [i for i in range(80) if self.seats[i] == 0]

        if len(available_seats) < required_seats:
            return None

        # Try to book seats in one row first
        for row_start in range(0, 80, 7):
            row_seats = [i for i in range(row_start, min(row_start + 7, 80)) if self.seats[i] == 0]
            if len(row_seats) >= required_seats:
                reserved = row_seats[:required_seats]
                self.update_seat_status(reserved)
                return reserved

        # If no row has enough seats, book the first available
        reserved = available_seats[:required_seats]
        self.update_seat_status(reserved)
        return reserved

    def update_seat_status(self, seat_ids):
        """Update the seat status to booked and save reservation to the database."""
        cursor = self.connection.cursor()
        for seat_id in seat_ids:
            self.seats[seat_id] = 1  # Update in memory
            cursor.execute("UPDATE seats SET status = 1 WHERE seat_id = ?", (seat_id,))
        cursor.execute("INSERT INTO reservations (seat_ids) VALUES (?)", (",".join(map(str, seat_ids)),))
        self.connection.commit()

    def count_available_seats(self):
        """Count and return the number of available seats."""
        return self.seats.count(0)

def main():
    st.title("Train Seat Reservation System")

    reservation_system = TrainSeatReservation()
    seat_display = reservation_system.display_seats()

    # Display current seat availability
    st.write("Current Seat Availability:")
    seat_display_str = " ".join(seat_display)
    st.text(seat_display_str.replace('O', '🟢').replace('X', '🔴'))

    # Show total available seats
    st.write(f"Total available seats: {reservation_system.count_available_seats()}")

    required_seats = st.number_input("Enter number of seats to reserve:", min_value=1, max_value=7)

    if st.button("Reserve Seats"):
        reserved_seats = reservation_system.book_seats(required_seats)
        if reserved_seats is not None:
            st.success(f"Seats booked successfully: {', '.join(str(s + 1) for s in reserved_seats)}")
            st.write(f"Total available seats after booking: {reservation_system.count_available_seats()}")
        else:
            st.error("Not enough seats available.")
    st.markdown("<footer style='text-align: center; padding: 20px;'>Made by Vaishwik Vishwakarma for Unstop Software Development Engineer assignment submission</footer>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
