import re

# 1. Add score_chart to ui.R
with open('app/ui.R', 'r') as f:
    ui_code = f.read()

old_btn_ui = '              shinycssloaders::withSpinner(DT::dataTableOutput("recommend_table"), type=8, color="#667eea", size=0.5)'
new_btn_ui = '              plotOutput("score_chart", height="200px"),\n              shinycssloaders::withSpinner(DT::dataTableOutput("recommend_table"), type=8, color="#667eea", size=0.5)'
ui_code = ui_code.replace(old_btn_ui, new_btn_ui)

with open('app/ui.R', 'w') as f:
    f.write(ui_code)

# 2. Add renderPlot to server.R
with open('app/server.R', 'r') as f:
    server_code = f.read()

# Insert before "output$recommend_table <- DT::renderDataTable({"
chart_code = """
    output$score_chart <- renderPlot({
      if (nrow(res_df) == 0) return(NULL)
      # Vẽ biểu đồ phân bố điểm số top 10
      top_n <- min(10, nrow(res_df))
      df_plot <- res_df[1:top_n, ]
      
      # Reverse order for horizontal bar chart
      df_plot <- df_plot[order(df_plot$score), ]
      
      par(mar=c(3, 10, 2, 2))
      barplot(df_plot$score, horiz=TRUE, names.arg=substring(df_plot$title, 1, 30),
              las=1, col="#667eea", border=NA, main="Top 10 Jobs: Match Score (%)",
              xlim=c(0, 100))
    })
    
"""

server_code = server_code.replace("    output$recommend_table <- DT::renderDataTable({", chart_code + "    output$recommend_table <- DT::renderDataTable({")

with open('app/server.R', 'w') as f:
    f.write(server_code)
