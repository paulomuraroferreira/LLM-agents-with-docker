Start the postgres with 
`systemctl status postgresql`

Switch to postgres user
`sudo -u postgres psql`

Alter password
`ALTER USER postgres WITH PASSWORD adminadmin`

Exit
`\q`

Log in
`sudo -u postgres psql`

Create Database
`CREATE DATABASE mydatabase;`

Exit
`\q`

Connect to database
`psql -U postgres -d mydatabase -W;`


Populate the database
`CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    sale_date DATE,
    quantity INT,
    unit_price NUMERIC
);`

Insert data
`INSERT INTO sales (sale_date, quantity, unit_price) VALUES
    ('2024-01-15', 100, 9.99),
    ('2024-01-16', 50, 24.99),
    ('2024-01-17', 75, 14.50);`


Verify
`SELECT * FROM sales;`




If the port is alredy in use, it will conflict with the langfuse port. So change the
langfuse port on /home/paulo/Python_projects/agents_docker/langfuse/docker-compose.yml from
5432 to 5433 on     

ports:
      - 5433:5432