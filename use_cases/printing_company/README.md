# DruckTech AG

## Overview
**DruckTech AG** is a global leader in industrial printing solutions, specializing in high-quality **offset and digital printing presses**, workflow automation, and post-press technologies. Our innovative solutions help print shops optimize efficiency, reduce waste, and achieve outstanding print quality. With a strong focus on **automation, digitalization, and sustainability**, DruckTech AG drives the future of modern printing. Decades of expertise and cutting-edge technology make us the trusted partner for the printing industry worldwide.

## Structured Data & Use Cases
This repository contains a **fictional dataset** from _DruckTech AG_. The dataset is split into three core tables that capture different aspects of the company’s printing operations:

1. **Customers**  
   Stores client information such as name, contact details, location, and phone numbers.  
   Example use: Identifying customer segments by country or city, generating targeted marketing campaigns, or pulling up client contact details on demand.

2. **Jobs**  
   Tracks printing jobs with columns for job name, priority, due date, and completion status.  
   Example use: Monitoring overall job status, identifying high-priority tasks, or finding overdue projects.

3. **Steps**  
   Details the step-by-step process for each job (e.g., _Prepare_, _Printing_, _Quality Checks_) along with timestamps.  
   Example use: Analyzing production workflows, calculating turnaround times for each step, or optimizing bottlenecks.

## Possible Business Use Cases

- **Customer Relationship Management**: Quickly view customers by region or generate lists of pending orders.
- **Production Tracking**: Identify high-priority jobs, check which steps are completed, or spot delays in real time.
- **Performance Analytics**: Calculate average lead times, track overall productivity, and improve scheduling and resource allocation.

## Untructured Data & Use Cases


## Example Questions
### Selected Services:
Make sure to select the following services for the questions to work:  
- **ANNUAL_REPORTS_SEARCH**
- **semantic_models/sales_orders.yaml**

### **Questions for Structured Data**
These queries operate on structured, tabular data sources.

| Question | Data Complexity | Level |
|----------|----------------|--------|
| What was the total order quantity per month with status shipped? | Single table, no Search Integration | 🟢 **Easy** |
| What was the total order quantity per month for United Kingdom with status shipped? | Single table, 1 Search Integration | 🟡 **Medium** |
| What was the order revenue per month for steel for my customer Delta? | 3 tables, 2 Search Integrations | 🔴 **Hard** |

### **Questions for Unstructured Data**  
These queries analyze text-based documents.

| Question | Data Complexity | Level |
|----------|----------------|--------|
| What were the latest AI innovations from Googol in 2024? | Single text chunk | 🟢 **Easy** |
| What was the net profit for Delta in 2024 and which people were part of the board? | Two chunks from one document | 🟡 **Medium** |
| What was the combined net profit for Googol and Delta in 2024 according to their annual reports? | Two chunks from two documents | 🔴 **Hard** |