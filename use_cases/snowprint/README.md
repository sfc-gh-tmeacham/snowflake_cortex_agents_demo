# SnowPrint AG

## Overview
**Snowprint AG** is a global leader in industrial printing solutions, specializing in high-quality **offset and digital printing presses**, workflow automation, and post-press technologies. Our innovative solutions help print shops optimize efficiency, reduce waste, and achieve outstanding print quality. With a strong focus on **automation, digitalization, and sustainability**, SnowPrint AG drives the future of modern printing. Decades of expertise and cutting-edge technology make us the trusted partner for the printing industry worldwide.

## Structured Data & Use Cases
This repository contains a **fictional dataset** from _Snowprint AG_. The dataset is split into three core tables that capture different aspects of the company’s printing operations:

1. **Customers**  
   Stores client information such as name, contact details, location, and phone numbers.  
   Example use: Identifying customer segments by country or city, generating targeted marketing campaigns, or pulling up client contact details on demand.

2. **Jobs**  
   Tracks printing jobs with columns for job name, priority, due date, and completion status.  
   Example use: Monitoring overall job status, identifying high-priority tasks, or finding overdue projects.

3. **Steps**  
   Details the step-by-step process for each job (e.g., _Prepare_, _Printing_, _Quality Checks_) along with timestamps.  
   Example use: Analyzing production workflows, calculating turnaround times for each step, or optimizing bottlenecks.

### Possible Business Use Cases

- **Customer Relationship Management**: Quickly view customers by region or generate lists of pending orders.
- **Production Tracking**: Identify high-priority jobs, check which steps are completed, or spot delays in real time.
- **Performance Analytics**: Calculate average lead times, track overall productivity, and improve scheduling and resource allocation.

## Unstructured Data & Use Cases
As an example, this demo contains two documents from _Heidelberger Druckmaschinen_:

| Filename                      | Description                                                                                                         |
|------------------------------ |---------------------------------------------------------------------------------------------------------------------|
| **Prinect_Quick_Start_CR_en.pdf** | A concise guide to the Prinect Manager workflow, covering job creation, user setup, and licensing with clear step-by-step examples. |
| **Color_Management_2019_en.pdf**  | An in-depth overview of color management, explaining ICC profiles, color spaces, and best practices for consistent print output.  |


### Possible Business Use Cases

- **Onboarding**: Accelerate the learning process for new team members by providing them with an intelligent assistant (🤖) that can address their questions in real time.  
- **Troubleshooting**: Quickly resolve common prepress or color management issues using established best practices and standardized configurations from the guides.  
- **Customer Support**: Offer immediate solutions to customers, eliminating lengthy wait times and reducing the need for direct expert intervention.

## Example Questions
### Selected Services:
Make sure to select the following services for the questions to work:  
- **SNOWPRINT_PRODUCT_GUIDES**
- **snowprint_customer_jobs.yaml**

### **Questions for Structured Data**
These queries operate on structured, tabular data sources.

| Question | Data Complexity | Query Complexity |
|----------|----------------|--------|
| Provide an overview per calendar week of how many print jobs are still pending. | Single table, no Search Integration | 🟢 **Easy** |
| Which customers in United Kingdom have the most jobs cancelled? Provide a top 10 list. | 2 tables, 1 Search Integration | 🟡 **Medium** |
| TBD | TBD | 🔴 **Hard** |

### **Questions for Unstructured Data**  
These queries analyze text-based documents.

| Question | Data Complexity | Query Complexity |
|----------|----------------|--------|
| What are the core components of the Prinect Manager CR workflow? | Single text chunk | 🟢 **Easy** |
| What are the basic steps for setting up users and customers? | 2 chunks from one document | 🟡 **Medium** |
| How does the standardized offset print process, including the use of a profile connection space, get operationalized within the Prinect Manager CR workflow during job creation and press calibration? | 4 chunks across two documents | 🔴 **Hard** |