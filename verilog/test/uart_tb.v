module test();
    reg clk = 0;
    reg uart_rx = 1;
    wire uart_tx;
    //
    reg [7:0] send_in;
    reg set_send;
    reg set_recv_clear;
    wire [7:0] recv_out;
    wire get_recv;

    uart #(8'd8) uut(
        .full_clk(clk),
        .uart_rx(uart_rx),
        .uart_tx(uart_tx),
        //
        .cpu_clk(cpu_clk),
        .send_in(send_in),
        .set_send(set_send),
        .set_recv_clear(set_recv_clear),
        .recv_out(recv_out),
        .get_recv(get_recv)
    );

    // CPU clock quarter speed of FPGA clock.
    reg [1:0] slow_CLK = 0;
    assign cpu_clk = slow_CLK[1];
    always @(posedge clk) begin
        slow_CLK <= slow_CLK + 1;
    end
    
    initial begin
        send_in = 0;
        set_send = 0;
        set_recv_clear = 0;
    end

    always
        #1 clk = ~clk;

    initial begin
        $display("Starting UART RX/TX");
        $monitor("recv_out=%b get_recv=%b", recv_out, get_recv);
        //$monitor("uart_tx=%b", uart_tx);
        //$monitor("uart_rx=%b", uart_rx);
        // Recieves some character?
        #10 uart_rx=0;
        #16 uart_rx=1;
        #16 uart_rx=0;
        #16 uart_rx=0;
        #16 uart_rx=0;
        #16 uart_rx=0;
        #16 uart_rx=1;
        #16 uart_rx=1;
        #16 uart_rx=0;
        #16 uart_rx=1;
        // Try send something!
        #64 send_in = "A"; // 65 0x41
        set_send =1;
        #16 set_send =0;
        #1 set_recv_clear = 1;
        //#4 btn=0;
        //#4 btn=1;
        #10000 $finish;
    end

    initial begin
        $dumpfile("uart.vcd");
        $dumpvars(0,test);
    end

endmodule