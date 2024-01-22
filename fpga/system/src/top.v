/*

Top level file for our system

*/

`include "../../verilog/src/fpga_leds.v"
`include "../../verilog/src/buttons.v"
`include "../../verilog/src/uart.v"
`include "../../verilog/src/clock.v"

`include "../../computer_fpga.v"

module top(
    input clk,
    output [5:0] led,
    input btn1,
    input btn2,
    output uartTx,
    input uartRx
);

    parameter SLOW=21; // 21 for debugging speed.
    wire rset;
    wire full_clk = clk;
    wire cpu_clk;
    wire resetn; // not used.

    wire run;
    wire zro;
    wire [7:0] status;
    wire btn;

    clock #(SLOW) clock(
        .CLK(full_clk),
        .RESET(rset),
        .clk(cpu_clk),
        .resetn(rsetn)
    );

    fpga_leds fpga_leds(
        .clk(cpu_clk),
        .run(run),
        .status(status),
        .zro(zro),
        .led(led)
    );

    buttons buttons(
        .clk(full_clk),
        .btn1(btn1),
        .btn2(btn2),
        .btn(btn),
        .reset(rset)
    );

    wire [7:0] send_in;
    wire set_send;
    wire set_recv_clear;
    wire [7:0] recv_out;
    wire get_recv;

    uart uart(
        .full_clk(full_clk),
        .uart_rx(uartRx),
        .uart_tx(uartTx),
        //
        .cpu_clk(cpu_clk),
        .send_in(send_in),
        .set_send(set_send),
        .set_recv_clear(set_recv_clear),
        .recv_out(recv_out),
        .get_recv(get_recv)
    );
 
    /* A basic test...
        on reset send 'R' to serial port
        on button press send 'B' to serial port
        on receive char from serial port send char to status display
    */

    reg [7:0] send_in_reg;
    reg set_send_reg;
    reg set_recv_clear_reg;
    reg [7:0] status_reg;

    initial begin
        send_in_reg = 0;
        set_send_reg = 1;
        set_recv_clear_reg = 0;
        status_reg = 0;
    end

    always @(posedge cpu_clk) begin
        if (rset) begin
            send_in_reg <= "R";
            set_send_reg <= 1;
        end
        else if (btn) begin
            send_in_reg <= "B";
            set_send_reg <= 1;
        end
        if (get_recv) begin
            status_reg <= recv_out;
            set_recv_clear_reg <= 1;
        end
    end

    assign send_in = send_in_reg;
    assign set_send = set_send_reg;
    assign set_recv_clear = set_recv_clear_reg;
    //assign recv_out = recv_out_reg;
    assign status = status_reg;
    assign run = cpu_clk;
    assign zro = full_clk;


endmodule